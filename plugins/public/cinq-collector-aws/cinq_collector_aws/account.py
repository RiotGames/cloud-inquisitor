from collections import defaultdict

from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from cloud_inquisitor import get_aws_session
from cloud_inquisitor.config import dbconfig, ConfigOption
from cloud_inquisitor.database import db
from cloud_inquisitor.exceptions import InquisitorError
from cloud_inquisitor.plugins import BaseCollector, CollectorType
from cloud_inquisitor.plugins.types.accounts import AWSAccount
from cloud_inquisitor.plugins.types.resources import S3Bucket, CloudFrontDist, DNSZone, DNSRecord, RDSInstance
from cloud_inquisitor.utils import get_resource_id
from cloud_inquisitor.wrappers import retry
import json


class AWSAccountCollector(BaseCollector):
    name = 'AWS Account Collector'
    ns = 'collector_ec2'
    type = CollectorType.AWS_ACCOUNT
    interval = dbconfig.get('interval', ns, 15)
    s3_collection_enabled = dbconfig.get('s3_bucket_collection', ns, True)
    cloudfront_collection_enabled = dbconfig.get('cloudfront_collection', ns, True)
    route53_collection_enabled = dbconfig.get('route53_collection', ns, True)
    rds_collection_enabled = dbconfig.get('rds_collection', ns, True)
    rds_function_name = dbconfig.get('rds_function_name', ns, '')
    rds_role = dbconfig.get('role_name', ns, 'default')
    rds_collector_account = dbconfig.get('rds_collector_account', ns, '')
    rds_collector_region = dbconfig.get('rds_collector_region', ns, '')
    rds_config_rule_name = dbconfig.get('rds_config_rule_name', ns, '')
    options = (
        ConfigOption('s3_bucket_collection', True, 'bool', 'Enable S3 Bucket Collection'),
        ConfigOption('cloudfront_collection', True, 'bool', 'Enable Cloudfront DNS Collection'),
        ConfigOption('route53_collection', True, 'bool', 'Enable Route53 DNS Collection'),
        ConfigOption('rds_collection', True, 'bool', 'Enable collection of RDS Databases'),
        ConfigOption('rds_function_name', '', 'string', 'Name of RDS Lambda Collector Function to execute'),
        ConfigOption('rds_role', '', 'string', 'Name of IAM role to assume in TARGET accounts'),
        ConfigOption('rds_collector_account', '', 'string', 'Account Name where RDS Lambda Collector runs'),
        ConfigOption('rds_collector_region', '', 'string', 'AWS Region where RDS Lambda Collector runs'),
        ConfigOption('rds_config_rule_name', '', 'string', 'Name of AWS Config rule to evaluate')
    )

    def __init__(self, account):
        super().__init__()

        if type(account) == str:
            account = AWSAccount.get(account)

        if not isinstance(account, AWSAccount):
            raise InquisitorError('The AWS Collector only supports AWS Accounts, got {}'.format(
                account.__class__.__name__
            ))

        self.account = account
        self.session = get_aws_session(self.account)

    def run(self):
        try:
            if self.s3_collection_enabled:
                self.update_s3buckets()

            if self.cloudfront_collection_enabled:
                self.update_cloudfront()

            if self.route53_collection_enabled:
                self.update_route53()

            if self.rds_collection_enabled:
                self.update_rds_databases()

        except Exception as ex:
            self.log.exception(ex)
            raise

        finally:
            del self.session

    @retry
    def update_rds_databases(self):
        """Update list of RDS Databases for the account / region

        Returns:
            `None`
        """
        self.log.info('Updating RDS Databases for {}'.format(
            self.account
        ))
        # All RDS resources are polled via a Lambda collector in a central account
        rds_collector_account = AWSAccount.get(self.rds_collector_account)
        rds_session = get_aws_session(rds_collector_account)
        # Existing RDS resources come from database
        existing_rds_dbs = RDSInstance.get_all(self.account)

        try:
            # Special session pinned to a single account for Lambda invocation so we
            # don't have to manage lambdas in every account & region
            lambda_client = rds_session.client('lambda', region_name=self.rds_collector_region)

            # The AWS Config Lambda will collect all the non-compliant resources for all regions
            # within the account
            input_payload = json.dumps({"account_id": self.account.account_number,
                                        "role": self.rds_role,
                                        "config_rule_name": self.rds_config_rule_name
                                        }).encode('utf-8')
            response = lambda_client.invoke(FunctionName=self.rds_function_name, InvocationType='RequestResponse',
                                            Payload=input_payload
                                            )
            rds_dbs = json.loads(response['Payload'].read().decode('utf-8'))

            for db_instance in rds_dbs:
                metrics = None
                if 'metrics' in db_instance.keys():
                    metrics = db_instance['metrics']
                tags = {t['Key']: t['Value'] for t in db_instance['tags'] or {}}
                properties = {
                    'tags': tags,
                    'metrics': metrics,
                    'creation_date': datetime.utcnow()
                }
                if db_instance['resource_name'] in existing_rds_dbs:
                    rds = existing_rds_dbs[db_instance['resource_name']]
                    if rds.update(db_instance, properties):
                        self.log.debug('Change detected for RDS instance {}/{} '
                                       .format(db_instance['resource_name'], properties))
                else:
                    RDSInstance.create(
                        db_instance['resource_name'],
                        account_id=self.account.account_id,
                        location=db_instance['location'],
                        properties=properties,
                        tags=tags
                    )
            db.session.commit()

            # Removal of RDS instances
            rk = set()
            erk = set()
            for database in rds_dbs:
                rk.add(database['resource_name'])
            for existing in existing_rds_dbs.keys():
                erk.add(existing)

            for resource_id in erk - rk:
                db.session.delete(existing_rds_dbs[resource_id].resource)
                self.log.debug('Removed RDS instances {}/{}'.format(
                    self.account.account_name,
                    resource_id
                ))
            db.session.commit()

        except Exception as e:
            self.log.exception('There was a problem during RDS collection for {}/{}'.format(
                self.account.account_name,
                e
            ))
            db.session.rollback()

    @retry
    def update_s3buckets(self):
        """Update list of S3 Buckets for the account

        Returns:
            `None`
        """
        self.log.debug('Updating S3Buckets for {}'.format(self.account.account_name))
        s3 = self.session.resource('s3')
        s3c = self.session.client('s3')

        try:
            existing_buckets = S3Bucket.get_all(self.account)
            buckets = {bucket.name: bucket for bucket in s3.buckets.all()}
            self.log.info('Buckets are {}'.format(buckets))
            for data in buckets.values():
                # This section ensures that we handle non-existent or non-accessible sub-resources
                try:
                    bucket_region = s3c.get_bucket_location(Bucket=data.name)['LocationConstraint']
                    if not bucket_region:
                        bucket_region = 'us-east-1'

                except ClientError as e:
                    self.log.info('Could not get bucket location..bucket possibly removed / {}'.format(e))
                    bucket_region = 'unavailable'

                try:
                    bucket_policy = data.Policy().policy

                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                        bucket_policy = None
                    else:
                        self.log.info('There was a problem collecting bucket policy for bucket {} on account {}, {}'
                                      .format(data.name, self.account, e.response))
                        bucket_policy = 'cinq cannot poll'

                try:
                    website_enabled = 'Enabled' if data.Website().index_document else 'Disabled'

                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchWebsiteConfiguration':
                        website_enabled = 'Disabled'
                    else:
                        self.log.info('There was a problem collecting website config for bucket {} on account {}'
                                      .format(data.name, self.account))
                        website_enabled = 'cinq cannot poll'

                try:
                    tags = {t['Key']: t['Value'] for t in data.Tagging().tag_set}

                except ClientError:
                    tags = {}

                try:
                    bucket_size = self._get_bucket_statistics(data.name, bucket_region, 'StandardStorage',
                                                              'BucketSizeBytes', 3)

                    bucket_obj_count = self._get_bucket_statistics(data.name, bucket_region, 'AllStorageTypes',
                                                                   'NumberOfObjects', 3)

                    metrics = {'size': bucket_size, 'object_count': bucket_obj_count}

                except Exception as e:
                    self.log.info('Could not retrieve bucket statistics / {}'.format(e))
                    metrics = {'found': False}

                properties = {
                    'bucket_policy': bucket_policy,
                    'creation_date': data.creation_date,
                    'location': bucket_region,
                    'website_enabled': website_enabled,
                    'metrics': metrics,
                    'tags': tags
                }

                if data.name in existing_buckets:
                    bucket = existing_buckets[data.name]
                    if bucket.update(data, properties):
                        self.log.debug('Change detected for S3Bucket {}/{}'.format(
                            self.account.account_name,
                            bucket.id
                        ))
                        bucket.save()
                else:
                    # If a bucket has no tags, a boto3 error is thrown. We treat this as an empty tag set

                    S3Bucket.create(
                        data.name,
                        account_id=self.account.account_id,
                        properties=properties,
                        location=bucket_region,
                        tags=tags
                    )
                    self.log.debug('Added new S3Bucket {}/{}'.format(
                        self.account.account_name,
                        data.name
                    ))
            db.session.commit()

            bk = set(list(buckets.keys()))
            ebk = set(list(existing_buckets.keys()))

            try:
                for resource_id in ebk - bk:
                    db.session.delete(existing_buckets[resource_id].resource)
                    self.log.debug('Deleted S3Bucket {}/{}'.format(
                        self.account.account_name,
                        resource_id
                    ))
                db.session.commit()

            except Exception as e:
                self.log.error(
                    'Could not update the current S3Bucket list for account {}/{}'.format(self.account.account_name, e))
                db.session.rollback()

        finally:
            del s3, s3c

    @retry
    def update_cloudfront(self):
        """Update list of CloudFront Distributions for the account

        Returns:
            `None`
        """
        self.log.debug('Updating CloudFront distributions for {}'.format(self.account.account_name))
        cfr = self.session.client('cloudfront')

        try:
            existing_dists = CloudFrontDist.get_all(self.account, None)
            dists = []

            # region Fetch information from API
            # region Web distributions
            done = False
            marker = None
            while not done:
                if marker:
                    response = cfr.list_distributions(Marker=marker)
                else:
                    response = cfr.list_distributions()

                dl = response['DistributionList']
                if dl['IsTruncated']:
                    marker = dl['NextMarker']
                else:
                    done = True

                if 'Items' in dl:
                    for dist in dl['Items']:
                        origins = []
                        for origin in dist['Origins']['Items']:
                            if 'S3OriginConfig' in origin:
                                origins.append(
                                    {
                                        'type': 's3',
                                        'source': origin['DomainName']
                                    }
                                )
                            elif 'CustomOriginConfig' in origin:
                                origins.append(
                                    {
                                        'type': 'custom-http',
                                        'source': origin['DomainName']
                                    }
                                )

                        data = {
                            'arn': dist['ARN'],
                            'name': dist['DomainName'],
                            'origins': origins,
                            'enabled': dist['Enabled'],
                            'type': 'web',
                            'tags': self.__get_distribution_tags(cfr, dist['ARN'])
                        }
                        dists.append(data)
            # endregion

            # region Streaming distributions
            done = False
            marker = None
            while not done:
                if marker:
                    response = cfr.list_streaming_distributions(Marker=marker)
                else:
                    response = cfr.list_streaming_distributions()

                dl = response['StreamingDistributionList']
                if dl['IsTruncated']:
                    marker = dl['NextMarker']
                else:
                    done = True

                if 'Items' in dl:
                    dists += [
                        {
                            'arn': x['ARN'],
                            'name': x['DomainName'],
                            'origins': [{'type': 's3', 'source': x['S3Origin']['DomainName']}],
                            'enabled': x['Enabled'],
                            'type': 'rtmp',
                            'tags': self.__get_distribution_tags(cfr, x['ARN'])
                        } for x in dl['Items']
                    ]
            # endregion
            # endregion

            for data in dists:
                if data['arn'] in existing_dists:
                    dist = existing_dists[data['arn']]
                    if dist.update(data):
                        self.log.debug('Updated CloudFrontDist {}/{}'.format(
                            self.account.account_name,
                            data['name']
                        ))
                        dist.save()

                else:
                    properties = {
                        'domain_name': data['name'],
                        'origins': data['origins'],
                        'enabled': data['enabled'],
                        'type': data['type']
                    }

                    CloudFrontDist.create(
                        data['arn'],
                        account_id=self.account.account_id,
                        properties=properties,
                        tags=data['tags']
                    )

                    self.log.debug('Added new CloudFrontDist {}/{}'.format(
                        self.account.account_name,
                        data['name']
                    ))
            db.session.commit()

            dk = set(x['arn'] for x in dists)
            edk = set(existing_dists.keys())

            try:
                for resource_id in edk - dk:
                    db.session.delete(existing_dists[resource_id].resource)
                    self.log.debug('Deleted CloudFrontDist {}/{}'.format(
                        resource_id,
                        self.account.account_name
                    ))
                db.session.commit()
            except:
                db.session.rollback()
        finally:
            del cfr

    @retry
    def update_route53(self):
        """Update list of Route53 DNS Zones and their records for the account

        Returns:
            `None`
        """
        self.log.debug('Updating Route53 information for {}'.format(self.account))

        # region Update zones
        existing_zones = DNSZone.get_all(self.account)
        zones = self.__fetch_route53_zones()
        for resource_id, data in zones.items():
            if resource_id in existing_zones:
                zone = DNSZone.get(resource_id)
                if zone.update(data):
                    self.log.debug('Change detected for Route53 zone {}/{}'.format(
                        self.account,
                        zone.name
                    ))
                    zone.save()
            else:
                tags = data.pop('tags')
                DNSZone.create(
                    resource_id,
                    account_id=self.account.account_id,
                    properties=data,
                    tags=tags
                )

                self.log.debug('Added Route53 zone {}/{}'.format(
                    self.account,
                    data['name']
                ))

        db.session.commit()

        zk = set(zones.keys())
        ezk = set(existing_zones.keys())

        for resource_id in ezk - zk:
            zone = existing_zones[resource_id]

            db.session.delete(zone.resource)
            self.log.debug('Deleted Route53 zone {}/{}'.format(
                self.account.account_name,
                zone.name.value
            ))
        db.session.commit()
        # endregion

        # region Update resource records
        try:
            for zone_id, zone in DNSZone.get_all(self.account).items():
                existing_records = {rec.id: rec for rec in zone.records}
                records = self.__fetch_route53_zone_records(zone.get_property('zone_id').value)

                for data in records:
                    if data['id'] in existing_records:
                        record = existing_records[data['id']]
                        if record.update(data):
                            self.log.debug('Changed detected for DNSRecord {}/{}/{}'.format(
                                self.account,
                                zone.name,
                                data['name']
                            ))
                            record.save()
                    else:
                        record = DNSRecord.create(
                            data['id'],
                            account_id=self.account.account_id,
                            properties={k: v for k, v in data.items() if k != 'id'},
                            tags={}
                        )
                        self.log.debug('Added new DNSRecord {}/{}/{}'.format(
                            self.account,
                            zone.name,
                            data['name']
                        ))
                        zone.add_record(record)
                db.session.commit()

                rk = set(x['id'] for x in records)
                erk = set(existing_records.keys())

                for resource_id in erk - rk:
                    record = existing_records[resource_id]
                    zone.delete_record(record)
                    self.log.debug('Deleted Route53 record {}/{}/{}'.format(
                        self.account.account_name,
                        zone_id,
                        record.name
                    ))
                db.session.commit()
        except:
            raise
        # endregion

    # region Helper functions
    @retry
    def __get_distribution_tags(self, client, arn):
        """Returns a dict containing the tags for a CloudFront distribution

        Args:
            client (botocore.client.CloudFront): Boto3 CloudFront client object
            arn (str): ARN of the distribution to get tags for

        Returns:
            `dict`
        """
        return {
            t['Key']: t['Value'] for t in client.list_tags_for_resource(
            Resource=arn
        )['Tags']['Items']
        }

    @retry
    def __fetch_route53_zones(self):
        """Return a list of all DNS zones hosted in Route53

        Returns:
            :obj:`list` of `dict`
        """
        done = False
        marker = None
        zones = {}
        route53 = self.session.client('route53')

        try:
            while not done:
                if marker:
                    response = route53.list_hosted_zones(Marker=marker)
                else:
                    response = route53.list_hosted_zones()

                if response['IsTruncated']:
                    marker = response['NextMarker']
                else:
                    done = True

                for zone_data in response['HostedZones']:
                    zones[get_resource_id('r53z', zone_data['Id'])] = {
                        'name': zone_data['Name'].rstrip('.'),
                        'source': 'AWS/{}'.format(self.account),
                        'comment': zone_data['Config']['Comment'] if 'Comment' in zone_data['Config'] else None,
                        'zone_id': zone_data['Id'],
                        'private_zone': zone_data['Config']['PrivateZone'],
                        'tags': self.__fetch_route53_zone_tags(zone_data['Id'])
                    }

            return zones
        finally:
            del route53

    @retry
    def __fetch_route53_zone_records(self, zone_id):
        """Return all resource records for a specific Route53 zone

        Args:
            zone_id (`str`): Name / ID of the hosted zone

        Returns:
            `dict`
        """
        route53 = self.session.client('route53')

        done = False
        nextName = nextType = None
        records = {}

        try:
            while not done:
                if nextName and nextType:
                    response = route53.list_resource_record_sets(
                        HostedZoneId=zone_id,
                        StartRecordName=nextName,
                        StartRecordType=nextType
                    )
                else:
                    response = route53.list_resource_record_sets(HostedZoneId=zone_id)

                if response['IsTruncated']:
                    nextName = response['NextRecordName']
                    nextType = response['NextRecordType']
                else:
                    done = True

                if 'ResourceRecordSets' in response:
                    for record in response['ResourceRecordSets']:
                        # Cannot make this a list, due to a race-condition in the AWS api that might return the same
                        # record more than once, so we use a dict instead to ensure that if we get duplicate records
                        # we simply just overwrite the one already there with the same info.
                        record_id = self._get_resource_hash(zone_id, record)
                        if 'AliasTarget' in record:
                            value = record['AliasTarget']['DNSName']
                            records[record_id] = {
                                'id': record_id,
                                'name': record['Name'].rstrip('.'),
                                'type': 'ALIAS',
                                'ttl': 0,
                                'value': [value]
                            }
                        else:
                            value = [y['Value'] for y in record['ResourceRecords']]
                            records[record_id] = {
                                'id': record_id,
                                'name': record['Name'].rstrip('.'),
                                'type': record['Type'],
                                'ttl': record['TTL'],
                                'value': value
                            }

            return list(records.values())
        finally:
            del route53

    @retry
    def __fetch_route53_zone_tags(self, zone_id):
        """Return a dict with the tags for the zone

        Args:
            zone_id (`str`): ID of the hosted zone

        Returns:
            :obj:`dict` of `str`: `str`
        """
        route53 = self.session.client('route53')

        try:
            return {
                tag['Key']: tag['Value'] for tag in
                route53.list_tags_for_resource(
                    ResourceType='hostedzone',
                    ResourceId=zone_id.split('/')[-1]
                )['ResourceTagSet']['Tags']
            }
        finally:
            del route53

    @staticmethod
    def _get_resource_hash(zone_name, record):
        """Returns the last ten digits of the sha256 hash of the combined arguments. Useful for generating unique
        resource IDs

        Args:
            zone_name (`str`): The name of the DNS Zone the record belongs to
            record (`dict`): A record dict to generate the hash from

        Returns:
            `str`
        """
        record_data = defaultdict(int, record)
        if type(record_data['GeoLocation']) == dict:
            record_data['GeoLocation'] = ":".join(["{}={}".format(k, v) for k, v in record_data['GeoLocation'].items()])

        args = [
            zone_name,
            record_data['Name'],
            record_data['Type'],
            record_data['Weight'],
            record_data['Region'],
            record_data['GeoLocation'],
            record_data['Failover'],
            record_data['HealthCheckId'],
            record_data['TrafficPolicyInstanceId']
        ]

        return get_resource_id('r53r', args)

    def _get_bucket_statistics(self, bucket_name, bucket_region, storage_type, statistic, days):
        """ Returns datapoints from cloudwatch for bucket statistics.

        Args:
            bucket_name `(str)`: The name of the bucket
            statistic `(str)`: The statistic you want to fetch from
            days `(int)`: Sample period for the statistic

        """

        cw = self.session.client('cloudwatch', region_name=bucket_region)

        # gather cw stats

        try:
            obj_stats = cw.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName=statistic,
                Dimensions=[
                    {
                        'Name': 'StorageType',
                        'Value': storage_type
                    },
                    {
                        'Name': 'BucketName',
                        'Value': bucket_name
                    }
                ],
                Period=86400,
                StartTime=datetime.utcnow() - timedelta(days=days),
                EndTime=datetime.utcnow(),
                Statistics=[
                    'Average'
                ]
            )
            stat_value = obj_stats['Datapoints'][0]['Average'] if obj_stats['Datapoints'] else 'NO_DATA'

            return stat_value

        except Exception as e:
            self.log.error(
                'Could not get bucket statistic for account {} / bucket {} / {}'.format(self.account.account_name,
                                                                                        bucket_name, e))

        finally:
            del cw

    # endregion
