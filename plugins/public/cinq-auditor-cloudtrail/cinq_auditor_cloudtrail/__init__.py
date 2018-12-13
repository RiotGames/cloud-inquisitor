import json

from botocore.exceptions import ClientError
from cloud_inquisitor import get_aws_session, AWS_REGIONS
from cloud_inquisitor.config import dbconfig, ConfigOption
from cloud_inquisitor.constants import NS_AUDITOR_CLOUDTRAIL
from cloud_inquisitor.log import auditlog
from cloud_inquisitor.plugins import BaseAuditor
from cloud_inquisitor.plugins.types.accounts import AWSAccount
from cloud_inquisitor.utils import get_template
from cloud_inquisitor.wrappers import retry


class CloudTrailAuditor(BaseAuditor):
    """CloudTrail auditor

    Ensures that CloudTrail is enabled and logging to a central location and that SNS/SQS notifications are enabled
    and being sent to the correct queues for the CloudTrail Logs application
    """

    name = 'CloudTrail'
    ns = NS_AUDITOR_CLOUDTRAIL
    interval = dbconfig.get('interval', ns, 60)
    options = (
        ConfigOption('enabled', False, 'bool', 'Enable the Cloudtrail auditor'),
        ConfigOption('interval', 60, 'int', 'Run frequency in minutes'),
        ConfigOption(
            'bucket_account',
            'CHANGE ME',
            'string',
            'Name of the account in which to create the S3 bucket where CloudTrail logs will be delivered. '
            'The account must exist in the accounts section of the tool'
        ),
        ConfigOption('bucket_name', 'CHANGE ME', 'string', 'Name of the S3 bucket to send CloudTrail logs to'),
        ConfigOption('bucket_region', 'us-west-2', 'string', 'Region for the S3 bucket for CloudTrail logs'),
        ConfigOption('global_cloudtrail_region', 'us-west-2', 'string', 'Region where to enable the global Cloudtrail'),
        ConfigOption('sns_topic_name', 'CHANGE ME', 'string', 'Name of the SNS topic for CloudTrail log delivery'),
        ConfigOption(
            'sqs_queue_account',
            'CHANGE ME',
            'string',
            'Name of the account which owns the SQS queue for CloudTrail log delivery notifications. '
            'This account must exist in the accounts section of the tool'
        ),
        ConfigOption('sqs_queue_name', 'SET ME', 'string', 'Name of the SQS queue'),
        ConfigOption('sqs_queue_region', 'us-west-2', 'string', 'Region for the SQS queue'),
        ConfigOption('trail_name', 'Cinq_Auditing', 'string', 'Name of the CloudTrail trail to create'),
    )

    def run(self, *args, **kwargs):
        """Entry point for the scheduler

        Args:
            *args: Optional arguments
            **kwargs: Optional keyword arguments

        Returns:
            None
        """
        accounts = list(AWSAccount.get_all(include_disabled=False).values())

        # S3 Bucket config
        s3_acl = get_template('cloudtrail_s3_bucket_policy.json')
        s3_bucket_name = self.dbconfig.get('bucket_name', self.ns)
        s3_bucket_region = self.dbconfig.get('bucket_region', self.ns, 'us-west-2')
        s3_bucket_account = AWSAccount.get(self.dbconfig.get('bucket_account', self.ns))
        CloudTrail.create_s3_bucket(s3_bucket_name, s3_bucket_region, s3_bucket_account, s3_acl)

        self.validate_sqs_policy(accounts)

        for account in accounts:
            ct = CloudTrail(account, s3_bucket_name, s3_bucket_region, self.log)
            ct.run()

    def validate_sqs_policy(self, accounts):
        """Given a list of accounts, ensures that the SQS policy allows all the accounts to write to the queue

        Args:
            accounts (`list` of :obj:`Account`): List of accounts

        Returns:
            `None`
        """
        sqs_queue_name = self.dbconfig.get('sqs_queue_name', self.ns)
        sqs_queue_region = self.dbconfig.get('sqs_queue_region', self.ns)
        sqs_account = AWSAccount.get(self.dbconfig.get('sqs_queue_account', self.ns))
        session = get_aws_session(sqs_account)

        sqs = session.client('sqs', region_name=sqs_queue_region)
        sqs_queue_url = sqs.get_queue_url(QueueName=sqs_queue_name, QueueOwnerAWSAccountId=sqs_account.account_number)
        sqs_attribs = sqs.get_queue_attributes(QueueUrl=sqs_queue_url['QueueUrl'], AttributeNames=['Policy'])

        policy = json.loads(sqs_attribs['Attributes']['Policy'])

        for account in accounts:
            arn = 'arn:aws:sns:*:{}:{}'.format(account.account_number, sqs_queue_name)
            if arn not in policy['Statement'][0]['Condition']['ForAnyValue:ArnEquals']['aws:SourceArn']:
                self.log.warning('SQS policy is missing condition for ARN {}'.format(arn))
                policy['Statement'][0]['Condition']['ForAnyValue:ArnEquals']['aws:SourceArn'].append(arn)

        sqs.set_queue_attributes(QueueUrl=sqs_queue_url['QueueUrl'], Attributes={'Policy': json.dumps(policy)})


class CloudTrail(object):
    """CloudTrail object"""
    ns = 'auditor_cloudtrail'

    def __init__(self, account, bucket_name, bucket_region, logger):
        self.account = account
        self.bucket_region = bucket_region
        self.bucket_name = bucket_name
        self.log = logger

        # Config settings
        self.global_ct_region = dbconfig.get('global_cloudtrail_region', self.ns, 'us-west-2')
        self.topic_name = dbconfig.get('sns_topic_name', self.ns, 'cloudtrail-log-notification')
        self.trail_name = dbconfig.get('trail_name', self.ns)

        sqs_queue_name = dbconfig.get('sqs_queue_name', self.ns)
        sqs_queue_region = dbconfig.get('sqs_queue_region', self.ns)
        sqs_account = AWSAccount.get(dbconfig.get('sqs_queue_account', self.ns))

        self.sqs_queue = 'arn:aws:sqs:{}:{}:{}'.format(
            sqs_queue_region,
            sqs_account.account_number,
            sqs_queue_name
        )

        self.session = get_aws_session(account)

    @retry
    def run(self):
        """Configures and enables a CloudTrail trail and logging on a single AWS Account.

        Has the capability to create both single region and multi-region trails.

        Will automatically create SNS topics, subscribe to SQS queues and turn on logging for the account in question,
        as well as reverting any manual changes to the trails if applicable.

        Returns:
            None
        """
        for aws_region in AWS_REGIONS:
            self.log.debug('Checking trails for {}/{}'.format(
                self.account.account_name,
                aws_region
            ))
            ct = self.session.client('cloudtrail', region_name=aws_region)
            trails = ct.describe_trails()

            if len(trails['trailList']) == 0:
                if aws_region == self.global_ct_region:
                    self.create_cloudtrail(aws_region)
            else:
                for trail in trails['trailList']:
                    if trail['Name'] in ('Default', self.trail_name):
                        if not trail['IsMultiRegionTrail']:
                            if trail['Name'] == self.trail_name and self.global_ct_region == aws_region:
                                ct.update_trail(
                                    Name=trail['Name'],
                                    IncludeGlobalServiceEvents=True,
                                    IsMultiRegionTrail=True
                                )
                                auditlog(
                                    event='cloudtrail.update_trail',
                                    actor=self.ns,
                                    data={
                                        'trailName': trail['Name'],
                                        'account': self.account.account_name,
                                        'region': aws_region,
                                        'changes': [
                                            {
                                                'setting': 'IsMultiRegionTrail',
                                                'oldValue': False,
                                                'newValue': True
                                            }
                                        ]
                                    }
                                )
                            else:
                                ct.delete_trail(name=trail['Name'])
                                auditlog(
                                    event='cloudtrail.delete_trail',
                                    actor=self.ns,
                                    data={
                                        'trailName': trail['Name'],
                                        'account': self.account.account_name,
                                        'region': aws_region,
                                        'reason': 'Incorrect region, name or not multi-regional'
                                    }
                                )
                        else:
                            if trail['HomeRegion'] == aws_region:
                                if self.global_ct_region != aws_region or trail['Name'] == 'Default':
                                    ct.delete_trail(Name=trail['Name'])
                                    auditlog(
                                        event='cloudtrail.delete_trail',
                                        actor=self.ns,
                                        data={
                                            'trailName': trail['Name'],
                                            'account': self.account.account_name,
                                            'region': aws_region,
                                            'reason': 'Incorrect name or region for multi-region trail'
                                        }
                                    )

            trails = ct.describe_trails()
            for trail in trails['trailList']:
                if trail['Name'] == self.trail_name and trail['HomeRegion'] == aws_region:
                    self.validate_trail_settings(ct, aws_region, trail)

    def validate_trail_settings(self, ct, aws_region, trail):
        """Validates logging, SNS and S3 settings for the global trail.

        Has the capability to:

        - start logging for the trail
        - create SNS topics & queues
        - configure or modify a S3 bucket for logging

        """
        self.log.debug('Validating trail {}/{}/{}'.format(
            self.account.account_name,
            aws_region,
            trail['Name']
        ))
        status = ct.get_trail_status(Name=trail['Name'])
        if not status['IsLogging']:
            self.log.warning('Logging is disabled for {}/{}/{}'.format(
                self.account.account_name,
                aws_region,
                trail['Name']
            ))
            self.start_logging(aws_region, trail['Name'])

        if 'SnsTopicName' not in trail or not trail['SnsTopicName']:
            self.log.warning('SNS Notifications not enabled for {}/{}/{}'.format(
                self.account.account_name,
                aws_region,
                trail['Name']
            ))
            self.create_sns_topic(aws_region)
            self.enable_sns_notification(aws_region, trail['Name'])

        if not self.validate_sns_topic_subscription(aws_region):
            self.log.warning(
                'SNS Notification configured but not subscribed for {}/{}/{}'.format(
                    self.account.account_name,
                    aws_region,
                    trail['Name']
                )
            )
            self.subscribe_sns_topic_to_sqs(aws_region)

        if trail['S3BucketName'] != self.bucket_name:
            self.log.warning('CloudTrail is logging to an incorrect bucket for {}/{}/{}'.format(
                self.account.account_name,
                trail['S3BucketName'],
                trail['Name']
            ))
            self.set_s3_bucket(aws_region, trail['Name'], self.bucket_name)

        if not trail.get('S3KeyPrefix') or trail['S3KeyPrefix'] != self.account.account_name:
            self.log.warning('Missing or incorrect S3KeyPrefix for {}/{}/{}'.format(
                self.account.account_name,
                aws_region,
                trail['Name']
            ))
            self.set_s3_prefix(aws_region, trail['Name'])

    # region helper functions
    def create_sns_topic(self, region):
        """Creates an SNS topic if needed. Returns the ARN if the created SNS topic

        Args:
            region (str): Region name

        Returns:
            `str`
        """
        sns = self.session.client('sns', region_name=region)

        self.log.info('Creating SNS topic for {}/{}'.format(self.account, region))
        # Create the topic
        res = sns.create_topic(Name=self.topic_name)
        arn = res['TopicArn']

        # Allow CloudTrail to publish messages with a policy update
        tmpl = get_template('cloudtrail_sns_policy.json')
        policy = tmpl.render(region=region, account_id=self.account.account_number, topic_name=self.topic_name)
        sns.set_topic_attributes(TopicArn=arn, AttributeName='Policy', AttributeValue=policy)

        auditlog(
            event='cloudtrail.create_sns_topic',
            actor=self.ns,
            data={
                'account': self.account.account_name,
                'region': region
            }
        )

        return arn

    def validate_sns_topic_subscription(self, region):
        """Validates SQS subscription to the SNS topic. Returns `True` if subscribed or `False` if not subscribed
        or topic is missing

        Args:
            region (str): Name of AWS Region

        Returns:
            `bool`
        """
        sns = self.session.client('sns', region_name=region)
        arn = 'arn:aws:sns:{}:{}:{}'.format(region, self.account.account_number, self.topic_name)
        try:
            data = sns.list_subscriptions_by_topic(TopicArn=arn)
        except ClientError as ex:
            self.log.error('Failed to list subscriptions by topic in {} ({}): {}'.format(
                self.account.account_name,
                region,
                ex
            ))
            return False

        for sub in data['Subscriptions']:
            if sub['Endpoint'] == self.sqs_queue:
                if sub['SubscriptionArn'] == 'PendingConfirmation':
                    self.log.warning('Subscription pending confirmation for {} in {}'.format(
                        self.account.account_name,
                        region
                    ))
                    return False
                return True

        return False

    def subscribe_sns_topic_to_sqs(self, region):
        """Subscribe SQS to the SNS topic. Returns the ARN of the SNS Topic subscribed

        Args:
            region (`str`): Name of the AWS region

        Returns:
            `str`
        """
        sns = self.session.resource('sns', region_name=region)
        topic = sns.Topic('arn:aws:sns:{}:{}:{}'.format(region, self.account.account_number, self.topic_name))

        topic.subscribe(Protocol='sqs', Endpoint=self.sqs_queue)

        auditlog(
            event='cloudtrail.subscribe_sns_topic_to_sqs',
            actor=self.ns,
            data={
                'account': self.account.account_name,
                'region': region
            }
        )

        return topic.attributes['TopicArn']

    def create_cloudtrail(self, region):
        """Creates a new CloudTrail Trail

        Args:
            region (str): Name of the AWS region

        Returns:
            `None`
        """
        ct = self.session.client('cloudtrail', region_name=region)

        # Creating the sns topic for the trail prior to creation
        self.create_sns_topic(region)

        ct.create_trail(
            Name=self.trail_name,
            S3BucketName=self.bucket_name,
            S3KeyPrefix=self.account.account_name,
            IsMultiRegionTrail=True,
            IncludeGlobalServiceEvents=True,
            SnsTopicName=self.topic_name
        )
        self.subscribe_sns_topic_to_sqs(region)

        auditlog(
            event='cloudtrail.create_cloudtrail',
            actor=self.ns,
            data={
                'account': self.account.account_name,
                'region': region
            }
        )
        self.log.info('Created CloudTrail for {} in {} ({})'.format(self.account, region, self.bucket_name))

    def enable_sns_notification(self, region, trailName):
        """Enable SNS notifications for a Trail

        Args:
            region (`str`): Name of the AWS region
            trailName (`str`): Name of the CloudTrail Trail

        Returns:
            `None`
        """
        ct = self.session.client('cloudtrail', region_name=region)
        ct.update_trail(Name=trailName, SnsTopicName=self.topic_name)

        auditlog(
            event='cloudtrail.enable_sns_notification',
            actor=self.ns,
            data={
                'account': self.account.account_name,
                'region': region
            }
        )
        self.log.info('Enabled SNS notifications for trail {} in {}/{}'.format(
            trailName,
            self.account.account_name,
            region
        ))

    def start_logging(self, region, name):
        """Turn on logging for a CloudTrail Trail

        Args:
            region (`str`): Name of the AWS region
            name (`str`): Name of the CloudTrail Trail

        Returns:
            `None`
        """
        ct = self.session.client('cloudtrail', region_name=region)
        ct.start_logging(Name=name)

        auditlog(
            event='cloudtrail.start_logging',
            actor=self.ns,
            data={
                'account': self.account.account_name,
                'region': region
            }
        )
        self.log.info('Enabled logging for {} ({})'.format(name, region))

    def set_s3_prefix(self, region, name):
        """Sets the S3 prefix for a CloudTrail Trail

        Args:
            region (`str`): Name of the AWS region
            name (`str`): Name of the CloudTrail Trail

        Returns:
            `None`
        """
        ct = self.session.client('cloudtrail', region_name=region)
        ct.update_trail(Name=name, S3KeyPrefix=self.account.account_name)

        auditlog(
            event='cloudtrail.set_s3_prefix',
            actor=self.ns,
            data={
                'account': self.account.account_name,
                'region': region
            }
        )
        self.log.info('Updated S3KeyPrefix to {0} for {0}/{1}'.format(
            self.account.account_name,
            region
        ))

    def set_s3_bucket(self, region, name, bucketName):
        """Sets the S3 bucket location for logfile delivery

        Args:
            region (`str`): Name of the AWS region
            name (`str`): Name of the CloudTrail Trail
            bucketName (`str`): Name of the S3 bucket to deliver log files to

        Returns:
            `None`
        """
        ct = self.session.client('cloudtrail', region_name=region)
        ct.update_trail(Name=name, S3BucketName=bucketName)

        auditlog(
            event='cloudtrail.set_s3_bucket',
            actor=self.ns,
            data={
                'account': self.account.account_name,
                'region': region
            }
        )
        self.log.info('Updated S3BucketName to {} for {} in {}/{}'.format(
            bucketName,
            name,
            self.account.account_name,
            region
        ))

    @classmethod
    def create_s3_bucket(cls, bucket_name, bucket_region, bucket_account, template):
        """Creates the S3 bucket on the account specified as the destination account for log files

        Args:
            bucket_name (`str`): Name of the S3 bucket
            bucket_region (`str`): AWS Region for the bucket
            bucket_account (:obj:`Account`): Account to create the S3 bucket in
            template (:obj:`Template`): Jinja2 Template object for the bucket policy

        Returns:
            `None`
        """
        s3 = get_aws_session(bucket_account).client('s3', region_name=bucket_region)

        # Check to see if the bucket already exists and if we have access to it
        try:
            s3.head_bucket(Bucket=bucket_name)
        except ClientError as ex:
            status_code = ex.response['ResponseMetadata']['HTTPStatusCode']

            # Bucket exists and we do not have access
            if status_code == 403:
                raise Exception('Bucket {} already exists but we do not have access to it and so cannot continue'.format(
                    bucket_name
                ))

            # Bucket does not exist, lets create one
            elif status_code == 404:
                try:
                    s3.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={
                            'LocationConstraint': bucket_region
                        }
                    )

                    auditlog(
                        event='cloudtrail.create_s3_bucket',
                        actor=cls.ns,
                        data={
                            'account': bucket_account.account_name,
                            'bucket_region': bucket_region,
                            'bucket_name': bucket_name
                        }
                    )
                except Exception:
                    raise Exception('An error occured while trying to create the bucket, cannot continue')

        try:
            bucket_acl = template.render(
                bucket_name=bucket_name,
                account_id=bucket_account.account_number
            )
            s3.put_bucket_policy(Bucket=bucket_name, Policy=bucket_acl)

        except Exception as ex:
            raise Warning('An error occurred while setting bucket policy: {}'.format(ex))
    # endregion
