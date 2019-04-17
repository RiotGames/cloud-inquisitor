from datetime import datetime
import json
from cloud_inquisitor import get_aws_session
from cloud_inquisitor.config import dbconfig, ConfigOption
from cloud_inquisitor.database import db
from cloud_inquisitor.exceptions import InquisitorError
from cloud_inquisitor.plugins import BaseCollector, CollectorType
from cloud_inquisitor.plugins.types.accounts import AWSAccount
from cloud_inquisitor.plugins.types.resources import EC2Instance, EBSVolume, EBSSnapshot, AMI, BeanStalk, VPC, RDSInstance
from cloud_inquisitor.utils import to_utc_date, isoformat, parse_date
from cloud_inquisitor.wrappers import retry
from cinq_collector_aws.resources import ELB


class AWSRegionCollector(BaseCollector):
    name = 'AWS Region Collector'
    ns = 'collector_ec2'
    type = CollectorType.AWS_REGION
    interval = dbconfig.get('interval', ns, 15)
    ec2_collection_enabled = dbconfig.get('ec2_instance_collection', ns, True)
    beanstalk_collection_enabled = dbconfig.get('beanstalk_collection', ns, True)
    vpc_collection_enabled = dbconfig.get('vpc_collection', ns, True)
    elb_collection_enabled = dbconfig.get('elb_collection', ns, True)
    rds_collection_enabled = dbconfig.get('rds_collection', ns, True)
    rds_function_name = dbconfig.get('rds_function_name', ns, '')
    rds_role = dbconfig.get('rds_role', ns, 'infosec_audits')
    rds_collector_account = dbconfig.get('rds_collector_account', ns, '')
    rds_collector_region = dbconfig.get('rds_collector_region', ns, '')
    rds_config_rule_name = dbconfig.get('rds_config_rule_name', ns, '')
    options = (
        ConfigOption('enabled', True, 'bool', 'Enable the AWS Region-based Collector'),
        ConfigOption('interval', 15, 'int', 'Run frequency, in minutes'),
        ConfigOption('max_instances', 1000, 'int', 'Maximum number of instances per API call'),
        ConfigOption('ec2_instance_collection', True, 'bool', 'Enable collection of Instance-Related Resources'),
        ConfigOption('beanstalk_collection', True, 'bool', 'Enable collection of Elastic Beanstalks'),
        ConfigOption('vpc_collection', True, 'bool', 'Enable collection of VPC Information'),
        ConfigOption('elb_collection', True, 'bool', 'Enable collection of ELBs'),
        ConfigOption('rds_collection', True, 'bool', 'Enable collection of RDS Databases'),
        ConfigOption('rds_function_name', '', 'string', 'Name of RDS Lambda Collector Function to execute'),
        ConfigOption('rds_role', '', 'string', 'Name of IAM role to assume in TARGET accounts'),
        ConfigOption('rds_collector_account', '', 'string', 'Account Name where RDS Lambda Collector runs'),
        ConfigOption('rds_collector_region', '', 'string', 'AWS Region where RDS Lambda Collector runs'),
        ConfigOption('rds_config_rule_name', '', 'string', 'Name of AWS Config rule to evaluate')
    )

    def __init__(self, account, region):
        super().__init__()

        if type(account) == str:
            account = AWSAccount.get(account)

        if not isinstance(account, AWSAccount):
            raise InquisitorError('The AWS Collector only supports AWS Accounts, got {}'.format(
                account.__class__.__name__
            ))

        self.account = account
        self.region = region
        self.session = get_aws_session(self.account)

    def run(self, *args, **kwargs):
        try:
            if self.ec2_collection_enabled:
                self.update_instances()
                self.update_volumes()
                self.update_snapshots()
                self.update_amis()

            if self.beanstalk_collection_enabled:
                self.update_beanstalks()

            if self.vpc_collection_enabled:
                self.update_vpcs()

            if self.elb_collection_enabled:
                self.update_elbs()

            if self.rds_collection_enabled:
                self.update_rds_databases()

        except Exception as ex:
            self.log.exception(ex)
            raise

        finally:
            del self.session

    @retry
    def update_instances(self):
        """Update list of EC2 Instances for the account / region

        Returns:
            `None`
        """
        self.log.debug('Updating EC2Instances for {}/{}'.format(self.account.account_name, self.region))
        ec2 = self.session.resource('ec2', region_name=self.region)

        try:
            existing_instances = EC2Instance.get_all(self.account, self.region)
            instances = {}
            api_instances = {x.id: x for x in ec2.instances.all()}

            try:
                for instance_id, data in api_instances.items():
                    if data.instance_id in existing_instances:
                        instance = existing_instances[instance_id]

                        if data.state['Name'] not in ('terminated', 'shutting-down'):
                            instances[instance_id] = instance

                            # Add object to transaction if it changed
                            if instance.update(data):
                                self.log.debug('Updating info for instance {} in {}/{}'.format(
                                    instance.resource.resource_id,
                                    self.account.account_name,
                                    self.region
                                ))
                                db.session.add(instance.resource)
                    else:
                        # New instance, if its not in state=terminated
                        if data.state['Name'] in ('terminated', 'shutting-down'):
                            continue

                        tags = {tag['Key']: tag['Value'] for tag in data.tags or {}}
                        properties = {
                            'launch_date': to_utc_date(data.launch_time).isoformat(),
                            'state': data.state['Name'],
                            'instance_type': data.instance_type,
                            'public_ip': getattr(data, 'public_ip_address', None),
                            'public_dns': getattr(data, 'public_dns_address', None),
                            'created': isoformat(datetime.now())
                        }

                        instance = EC2Instance.create(
                            data.instance_id,
                            account_id=self.account.account_id,
                            location=self.region,
                            properties=properties,
                            tags=tags
                        )

                        instances[instance.resource.resource_id] = instance
                        self.log.debug('Added new EC2Instance {}/{}/{}'.format(
                            self.account.account_name,
                            self.region,
                            instance.resource.resource_id
                        ))

                # Check for deleted instances
                ik = set(list(instances.keys()))
                eik = set(list(existing_instances.keys()))

                for instanceID in eik - ik:
                    db.session.delete(existing_instances[instanceID].resource)
                    self.log.debug('Deleted EC2Instance {}/{}/{}'.format(
                        self.account.account_name,
                        self.region,
                        instanceID
                    ))

                db.session.commit()
            except:
                db.session.rollback()
                raise
        finally:
            del ec2

    @retry
    def update_amis(self):
        """Update list of AMIs for the account / region

        Returns:
            `None`
        """
        self.log.debug('Updating AMIs for {}/{}'.format(self.account.account_name, self.region))
        ec2 = self.session.resource('ec2', region_name=self.region)

        try:
            existing_images = AMI.get_all(self.account, self.region)
            images = {x.id: x for x in ec2.images.filter(Owners=['self'])}

            for data in list(images.values()):
                if data.id in existing_images:
                    ami = existing_images[data.id]
                    if ami.update(data):
                        self.log.debug('Changed detected for AMI {}/{}/{}'.format(
                            self.account.account_name,
                            self.region,
                            ami.resource.resource_id
                        ))
                else:
                    properties = {
                        'architecture': data.architecture,
                        'creation_date': parse_date(data.creation_date or '1970-01-01 00:00:00'),
                        'description': data.description,
                        'name': data.name,
                        'platform': data.platform or 'Linux',
                        'state': data.state,
                    }
                    tags = {tag['Key']: tag['Value'] for tag in data.tags or {}}

                    AMI.create(
                        data.id,
                        account_id=self.account.account_id,
                        location=self.region,
                        properties=properties,
                        tags=tags
                    )

                    self.log.debug('Added new AMI {}/{}/{}'.format(
                        self.account.account_name,
                        self.region,
                        data.id
                    ))
            db.session.commit()

            # Check for deleted instances
            ik = set(list(images.keys()))
            eik = set(list(existing_images.keys()))

            try:
                for image_id in eik - ik:
                    db.session.delete(existing_images[image_id].resource)
                    self.log.debug('Deleted AMI {}/{}/{}'.format(
                        self.account.account_name,
                        self.region,
                        image_id,
                    ))

                db.session.commit()
            except:
                db.session.rollback()
        finally:
            del ec2

    @retry
    def update_volumes(self):
        """Update list of EBS Volumes for the account / region

        Returns:
            `None`
        """
        self.log.debug('Updating EBSVolumes for {}/{}'.format(self.account.account_name, self.region))
        ec2 = self.session.resource('ec2', region_name=self.region)

        try:
            existing_volumes = EBSVolume.get_all(self.account, self.region)
            volumes = {x.id: x for x in ec2.volumes.all()}

            for data in list(volumes.values()):
                if data.id in existing_volumes:
                    vol = existing_volumes[data.id]
                    if vol.update(data):
                        self.log.debug('Changed detected for EBSVolume {}/{}/{}'.format(
                            self.account.account_name,
                            self.region,
                            vol.resource.resource_id
                        ))

                else:
                    properties = {
                        'create_time': data.create_time,
                        'encrypted': data.encrypted,
                        'iops': data.iops or 0,
                        'kms_key_id': data.kms_key_id,
                        'size': data.size,
                        'state': data.state,
                        'snapshot_id': data.snapshot_id,
                        'volume_type': data.volume_type,
                        'attachments': sorted([x['InstanceId'] for x in data.attachments])
                    }
                    tags = {t['Key']: t['Value'] for t in data.tags or {}}
                    vol = EBSVolume.create(
                        data.id,
                        account_id=self.account.account_id,
                        location=self.region,
                        properties=properties,
                        tags=tags
                    )

                    self.log.debug('Added new EBSVolume {}/{}/{}'.format(
                        self.account.account_name,
                        self.region,
                        vol.resource.resource_id
                    ))
            db.session.commit()

            vk = set(list(volumes.keys()))
            evk = set(list(existing_volumes.keys()))
            try:
                for volumeID in evk - vk:
                    db.session.delete(existing_volumes[volumeID].resource)
                    self.log.debug('Deleted EBSVolume {}/{}/{}'.format(
                        volumeID,
                        self.account.account_name,
                        self.region
                    ))

                db.session.commit()
            except:
                self.log.exception('Failed removing deleted volumes')
                db.session.rollback()
        finally:
            del ec2

    @retry
    def update_snapshots(self):
        """Update list of EBS Snapshots for the account / region

        Returns:
            `None`
        """
        self.log.debug('Updating EBSSnapshots for {}/{}'.format(self.account.account_name, self.region))
        ec2 = self.session.resource('ec2', region_name=self.region)

        try:
            existing_snapshots = EBSSnapshot.get_all(self.account, self.region)
            snapshots = {x.id: x for x in ec2.snapshots.filter(OwnerIds=[self.account.account_number])}

            for data in list(snapshots.values()):
                if data.id in existing_snapshots:
                    snapshot = existing_snapshots[data.id]
                    if snapshot.update(data):
                        self.log.debug('Change detected for EBSSnapshot {}/{}/{}'.format(
                            self.account.account_name,
                            self.region,
                            snapshot.resource.resource_id
                        ))

                else:
                    properties = {
                        'create_time': data.start_time,
                        'encrypted': data.encrypted,
                        'kms_key_id': data.kms_key_id,
                        'state': data.state,
                        'state_message': data.state_message,
                        'volume_id': data.volume_id,
                        'volume_size': data.volume_size,
                    }
                    tags = {t['Key']: t['Value'] for t in data.tags or {}}

                    snapshot = EBSSnapshot.create(
                        data.id,
                        account_id=self.account.account_id,
                        location=self.region,
                        properties=properties,
                        tags=tags
                    )

                    self.log.debug('Added new EBSSnapshot {}/{}/{}'.format(
                        self.account.account_name,
                        self.region,
                        snapshot.resource.resource_id
                    ))

            db.session.commit()

            vk = set(list(snapshots.keys()))
            evk = set(list(existing_snapshots.keys()))
            try:
                for snapshotID in evk - vk:
                    db.session.delete(existing_snapshots[snapshotID].resource)
                    self.log.debug('Deleted EBSSnapshot {}/{}/{}'.format(
                        self.account.account_name,
                        self.region,
                        snapshotID
                    ))

                db.session.commit()
            except:
                self.log.exception('Failed removing deleted snapshots')
                db.session.rollback()
        finally:
            del ec2

    @retry
    def update_beanstalks(self):
        """Update list of Elastic BeanStalks for the account / region

        Returns:
            `None`
        """
        self.log.debug('Updating ElasticBeanStalk environments for {}/{}'.format(
            self.account.account_name,
            self.region
        ))
        ebclient = self.session.client('elasticbeanstalk', region_name=self.region)

        try:
            existing_beanstalks = BeanStalk.get_all(self.account, self.region)
            beanstalks = {}
            # region Fetch elastic beanstalks
            for env in ebclient.describe_environments()['Environments']:
                # Only get information for HTTP (non-worker) Beanstalks
                if env['Tier']['Type'] == 'Standard':
                    if 'CNAME' in env:
                        beanstalks[env['EnvironmentId']] = {
                            'id': env['EnvironmentId'],
                            'environment_name': env['EnvironmentName'],
                            'application_name': env['ApplicationName'],
                            'cname': env['CNAME']
                        }
                    else:
                        self.log.warning('Found a BeanStalk that does not have a CNAME: {} in {}/{}'.format(
                            env['EnvironmentName'],
                            self.account,
                            self.region
                        ))
                else:
                    self.log.debug('Skipping worker tier ElasticBeanstalk environment {}/{}/{}'.format(
                        self.account.account_name,
                        self.region,
                        env['EnvironmentName']
                    ))
            # endregion

            try:
                for data in beanstalks.values():
                    if data['id'] in existing_beanstalks:
                        beanstalk = existing_beanstalks[data['id']]
                        if beanstalk.update(data):
                            self.log.debug('Change detected for ElasticBeanStalk {}/{}/{}'.format(
                                self.account.account_name,
                                self.region,
                                data['id']
                            ))
                    else:
                        bid = data.pop('id')
                        tags = {}
                        BeanStalk.create(
                            bid,
                            account_id=self.account.account_id,
                            location=self.region,
                            properties=data,
                            tags=tags
                        )

                        self.log.debug('Added new ElasticBeanStalk {}/{}/{}'.format(
                            self.account.account_name,
                            self.region,
                            bid
                        ))
                db.session.commit()

                bk = set(beanstalks.keys())
                ebk = set(existing_beanstalks.keys())

                for resource_id in ebk - bk:
                    db.session.delete(existing_beanstalks[resource_id].resource)
                    self.log.debug('Deleted ElasticBeanStalk {}/{}/{}'.format(
                        self.account.account_name,
                        self.region,
                        resource_id
                    ))
                db.session.commit()
            except:
                db.session.rollback()

            return beanstalks
        finally:
            del ebclient

    @retry
    def update_vpcs(self):
        """Update list of VPCs for the account / region

        Returns:
            `None`
        """
        self.log.debug('Updating VPCs for {}/{}'.format(
            self.account.account_name,
            self.region
        ))

        existing_vpcs = VPC.get_all(self.account, self.region)
        try:
            ec2 = self.session.resource('ec2', region_name=self.region)
            ec2_client = self.session.client('ec2', region_name=self.region)
            vpcs = {x.id: x for x in ec2.vpcs.all()}

            for data in vpcs.values():
                flow_logs = ec2_client.describe_flow_logs(
                    Filters=[
                        {
                            'Name': 'resource-id',
                            'Values': [data.vpc_id]
                        }
                    ]
                ).get('FlowLogs')

                tags = {t['Key']: t['Value'] for t in data.tags or {}}
                properties = {
                    'vpc_id': data.vpc_id,
                    'cidr_v4': data.cidr_block,
                    'is_default': data.is_default,
                    'state': data.state,
                    'vpc_flow_logs_status': flow_logs[0]['FlowLogStatus'] if flow_logs else 'UNDEFINED',
                    'vpc_flow_logs_log_group': flow_logs[0]['LogGroupName'] if flow_logs else 'UNDEFINED',
                    'tags': tags
                }
                if data.id in existing_vpcs:
                    vpc = existing_vpcs[data.vpc_id]
                    if vpc.update(data, properties):
                        self.log.debug('Change detected for VPC {}/{}/{} '.format(data.vpc_id, self.region, properties))
                else:
                    VPC.create(
                        data.id,
                        account_id=self.account.account_id,
                        location=self.region,
                        properties=properties,
                        tags=tags
                    )
            db.session.commit()

            # Removal of VPCs
            vk = set(vpcs.keys())
            evk = set(existing_vpcs.keys())

            for resource_id in evk - vk:
                db.session.delete(existing_vpcs[resource_id].resource)
                self.log.debug('Removed VPCs {}/{}/{}'.format(
                    self.account.account_name,
                    self.region,
                    resource_id
                ))
            db.session.commit()

        except Exception:
            self.log.exception('There was a problem during VPC collection for {}/{}'.format(
                self.account.account_name,
                self.region
            ))
            db.session.rollback()

    @retry
    def update_elbs(self):
        """Update list of ELBs for the account / region

        Returns:
            `None`
        """
        self.log.debug('Updating ELBs for {}/{}'.format(
            self.account.account_name,
            self.region
        ))

        # ELBs known to CINQ
        elbs_from_db = ELB.get_all(self.account, self.region)
        try:

            # ELBs known to AWS
            elb_client = self.session.client('elb', region_name=self.region)
            load_balancer_instances = elb_client.describe_load_balancers()['LoadBalancerDescriptions']
            elbs_from_api = {}
            for load_balancer in load_balancer_instances:
                key = '{}::{}'.format(self.region, load_balancer['LoadBalancerName'])
                elbs_from_api[key] = load_balancer

            # Process ELBs known to AWS
            for elb_identifier in elbs_from_api:
                data = elbs_from_api[elb_identifier]
                # ELB already in DB?
                if elb_identifier in elbs_from_db:
                    elb = elbs_from_db[elb_identifier]
                    if elb.update(data):
                        self.log.info(
                            'Updating info for ELB {} in {}/{}'.format(
                                elb.resource.resource_id,
                                self.account.account_name,
                                self.region
                            )
                        )
                        db.session.add(elb.resource)
                else:
                    # Not previously seen this ELB, so add it
                    if 'Tags' in data:
                        try:
                            tags = {tag['Key']: tag['Value'] for tag in data['Tags']}
                        except AttributeError:
                            tags = {}
                    else:
                        tags = {}

                    vpc_data = (data['VPCId'] if ('VPCId' in data and data['VPCId']) else 'no vpc')

                    properties = {
                        'lb_name': data['LoadBalancerName'],
                        'dns_name': data['DNSName'],
                        'instances': ' '.join(
                            [instance['InstanceId'] for instance in data['Instances']]
                        ),
                        'num_instances': len(
                            [instance['InstanceId'] for instance in data['Instances']]
                        ),
                        'vpc_id': vpc_data,
                        'state': 'not_reported'
                    }
                    if 'CanonicalHostedZoneName' in data:
                        properties['canonical_hosted_zone_name'] = data['CanonicalHostedZoneName']
                    else:
                        properties['canonical_hosted_zone_name'] = None

                    # LoadBalancerName doesn't have to be unique across all regions
                    # Use region::LoadBalancerName as resource_id
                    resource_id = '{}::{}'.format(self.region, data['LoadBalancerName'])

                    # All done, create
                    elb = ELB.create(
                        resource_id,
                        account_id=self.account.account_id,
                        location=self.region,
                        properties=properties,
                        tags=tags
                    )

                    # elbs[elb.resource.resource_id] = elb
                    self.log.info(
                        'Added new ELB {}/{}/{}'.format(
                            self.account.account_name,
                            self.region,
                            elb.resource.resource_id
                        )
                    )

            # Delete no longer existing ELBs
            elb_keys_from_db = set(list(elbs_from_db.keys()))
            self.log.debug('elb_keys_from_db =  %s', elb_keys_from_db)
            elb_keys_from_api = set(list(elbs_from_api.keys()))
            self.log.debug('elb_keys_from_api = %s', elb_keys_from_api)

            for elb_identifier in elb_keys_from_db - elb_keys_from_api:
                db.session.delete(elbs_from_db[elb_identifier].resource)
                self.log.info('Deleted ELB {}/{}/{}'.format(
                    self.account.account_name,
                    self.region,
                    elb_identifier
                )
                )
            db.session.commit()


        except:
            self.log.exception('There was a problem during ELB collection for {}/{}'.format(
                self.account.account_name,
                self.region
            ))
            db.session.rollback()


    @retry
    def update_rds_databases(self):
        """Update list of RDS Databases for the account / region

        Returns:
            `None`
        """
        self.log.info('Updating RDS Databases for {} / {}'.format(
            self.account, self.region
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
                                        "region": self.region,
                                        "role": self.rds_role,
                                        "config_rule_name": self.rds_config_rule_name
                                        }).encode('utf-8')
            response = lambda_client.invoke(FunctionName=self.rds_function_name, InvocationType='RequestResponse',
                                            Payload=input_payload
                                            )
            rds_dbs = json.loads(response['Payload'].read().decode('utf-8'))['data']
            if 'errorMessage' in rds_dbs:
                self.log.error('RDS Lambda Execution Failed / {} / {} / {}'.
                                format(self.account.account_name, self.region, rds_dbs['errorMessage']))
                raise

            if rds_dbs:
                for db_instance in rds_dbs:
                    metrics = None
                    if 'metrics' in db_instance.keys():
                        metrics = db_instance['metrics']
                    tags = {t['Key']: t['Value'] for t in db_instance['tags'] or {}}
                    properties = {
                        'tags': tags,
                        'metrics': metrics,
                        'engine': rds_dbs['engine'],
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
                            location=db_instance['region'],
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
            self.log.exception('There was a problem during RDS collection for {}/{}/{}'.format(
                self.account.account_name, self.account.region, e
            ))
            db.session.rollback()
