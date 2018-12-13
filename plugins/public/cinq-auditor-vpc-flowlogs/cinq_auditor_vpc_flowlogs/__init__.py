from botocore.exceptions import ClientError
from cloud_inquisitor import get_aws_session, AWS_REGIONS
from cloud_inquisitor.config import dbconfig, ConfigOption
from cloud_inquisitor.constants import NS_AUDITOR_VPC_FLOW_LOGS
from cloud_inquisitor.database import db
from cloud_inquisitor.log import auditlog
from cloud_inquisitor.plugins import BaseAuditor
from cloud_inquisitor.plugins.types.accounts import AWSAccount
from cloud_inquisitor.plugins.types.resources import VPC
from cloud_inquisitor.utils import get_template
from cloud_inquisitor.wrappers import retry


class VPCFlowLogsAuditor(BaseAuditor):
    name = 'VPC Flow Log Compliance'
    ns = NS_AUDITOR_VPC_FLOW_LOGS
    interval = dbconfig.get('interval', ns, 60)
    role_name = dbconfig.get('role_name', ns, 'VpcFlowLogsRole')
    start_delay = 0
    options = (
        ConfigOption('enabled', False, 'bool', 'Enable the VPC Flow Logs auditor'),
        ConfigOption('interval', 60, 'int', 'Run frequency in minutes'),
        ConfigOption('role_name', 'VpcFlowLogsRole', 'str', 'Name of IAM Role used for VPC Flow Logs')
    )

    def __init__(self):
        super().__init__()
        self.session = None

    def run(self):
        """Main entry point for the auditor worker.

        Returns:
            `None`
        """
        # Loop through all accounts that are marked as enabled
        accounts = list(AWSAccount.get_all(include_disabled=False).values())
        for account in accounts:
            self.log.debug('Updating VPC Flow Logs for {}'.format(account))

            self.session = get_aws_session(account)
            role_arn = self.confirm_iam_role(account)
            # region specific
            for aws_region in AWS_REGIONS:
                try:
                    vpc_list = VPC.get_all(account, aws_region).values()
                    need_vpc_flow_logs = [x for x in vpc_list if x.vpc_flow_logs_status != 'ACTIVE']

                    for vpc in need_vpc_flow_logs:
                        if self.confirm_cw_log(account, aws_region, vpc.id):
                            self.create_vpc_flow_logs(account, aws_region, vpc.id, role_arn)
                        else:
                            self.log.info('Failed to confirm log group for {}/{}'.format(
                                account,
                                aws_region
                            ))

                except Exception:
                    self.log.exception('Failed processing VPCs for {}/{}.'.format(
                        account,
                        aws_region
                    ))

            db.session.commit()

    @retry
    def confirm_iam_role(self, account):
        """Return the ARN of the IAM Role on the provided account as a string. Returns an `IAMRole` object from boto3

        Args:
            account (:obj:`Account`): Account where to locate the role

        Returns:
            :obj:`IAMRole`
        """
        try:
            iam = self.session.client('iam')
            rolearn = iam.get_role(RoleName=self.role_name)['Role']['Arn']
            return rolearn

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                self.create_iam_role(account)
            else:
                raise

        except Exception as e:
            self.log.exception('Failed validating IAM role for VPC Flow Log Auditing for {}'.format(e))


    @retry
    def create_iam_role(self, account):
        """Create a new IAM role. Returns the ARN of the newly created role

        Args:
            account (:obj:`Account`): Account where to create the IAM role

        Returns:
            `str`
        """
        try:
            iam = self.session.client('iam')
            trust = get_template('vpc_flow_logs_iam_role_trust.json').render()
            policy = get_template('vpc_flow_logs_role_policy.json').render()

            newrole = iam.create_role(
                Path='/',
                RoleName=self.role_name,
                AssumeRolePolicyDocument=trust
            )['Role']['Arn']

            # Attach an inline policy to the role to avoid conflicts or hitting the Managed Policy Limit
            iam.put_role_policy(
                RoleName=self.role_name,
                PolicyName='VpcFlowPolicy',
                PolicyDocument=policy
            )

            self.log.debug('Created VPC Flow Logs role & policy for {}'.format(account.account_name))
            auditlog(
                event='vpc_flow_logs.create_iam_role',
                actor=self.ns,
                data={
                    'account': account.account_name,
                    'roleName': self.role_name,
                    'trustRelationship': trust,
                    'inlinePolicy': policy
                }
            )
            return newrole

        except Exception:
            self.log.exception('Failed creating the VPC Flow Logs role for {}.'.format(account))

    @retry
    def confirm_cw_log(self, account, region, vpcname):
        """Create a new CloudWatch log group based on the VPC Name if none exists. Returns `True` if succesful

        Args:
            account (:obj:`Account`): Account to create the log group in
            region (`str`): Region to create the log group in
            vpcname (`str`): Name of the VPC the log group is fow

        Returns:
            `bool`
        """
        try:
            cw = self.session.client('logs', region)
            token = None
            log_groups = []
            while True:
                result = cw.describe_log_groups() if not token else cw.describe_log_groups(nextToken=token)
                token = result.get('nextToken')
                log_groups.extend([x['logGroupName'] for x in result.get('logGroups', [])])

                if not token:
                    break

            if vpcname not in log_groups:
                cw.create_log_group(logGroupName=vpcname)

                cw_vpc = VPC.get(vpcname)
                cw_vpc.set_property('vpc_flow_logs_log_group', vpcname)

                self.log.info('Created log group {}/{}/{}'.format(account.account_name, region, vpcname))
                auditlog(
                    event='vpc_flow_logs.create_cw_log_group',
                    actor=self.ns,
                    data={
                        'account': account.account_name,
                        'region': region,
                        'log_group_name': vpcname,
                        'vpc': vpcname
                    }
                )
            return True

        except Exception:
            self.log.exception('Failed creating log group for {}/{}/{}.'.format(
                account,
                region, vpcname
            ))

    @retry
    def create_vpc_flow_logs(self, account, region, vpc_id, iam_role_arn):
        """Create a new VPC Flow log

        Args:
            account (:obj:`Account`): Account to create the flow in
            region (`str`): Region to create the flow in
            vpc_id (`str`): ID of the VPC to create the flow for
            iam_role_arn (`str`): ARN of the IAM role used to post logs to the log group

        Returns:
            `None`
        """
        try:
            flow = self.session.client('ec2', region)
            flow.create_flow_logs(
                ResourceIds=[vpc_id],
                ResourceType='VPC',
                TrafficType='ALL',
                LogGroupName=vpc_id,
                DeliverLogsPermissionArn=iam_role_arn
            )
            fvpc = VPC.get(vpc_id)
            fvpc.set_property('vpc_flow_logs_status', 'ACTIVE')

            self.log.info('Enabled VPC Logging {}/{}/{}'.format(account, region, vpc_id))
            auditlog(
                event='vpc_flow_logs.create_vpc_flow',
                actor=self.ns,
                data={
                    'account': account.account_name,
                    'region': region,
                    'vpcId': vpc_id,
                    'arn': iam_role_arn
                }
            )
        except Exception:
            self.log.exception('Failed creating VPC Flow Logs for {}/{}/{}.'.format(
                account,
                region,
                vpc_id
            ))
