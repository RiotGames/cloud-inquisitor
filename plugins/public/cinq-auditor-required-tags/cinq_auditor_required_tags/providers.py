import json
import logging
from datetime import datetime, timedelta

from cinq_auditor_required_tags.utils import s3_removal_policy_exists, s3_removal_lifecycle_policy_exists
from cloud_inquisitor import get_aws_session
from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.constants import ActionStatus
from cloud_inquisitor.constants import AuditActions, NS_AUDITOR_REQUIRED_TAGS
from cloud_inquisitor.log import auditlog
from cloud_inquisitor.plugins.types.accounts import AWSAccount
from cloud_inquisitor.plugins.types.enforcements import Enforcement
from cloud_inquisitor.plugins.types.resources import EC2Instance

logger = logging.getLogger(__name__)


def noop(client, resource):
    return ActionStatus.SUCCEED, resource.metrics()


def process_action(resource, action, action_issuer='unknown'):
    """Process an audit action for a resource, if possible

    Args:
        resource (:obj:`Resource`): A resource object to perform the action on
        action (`str`): Type of action to perform (`kill` or `stop`)
        action_issuer (`str`): The issuer of the action
    Returns:
        `ActionStatus`
    """
    func_action = action_mapper[resource.resource_type][action]
    extra_info = {}
    if func_action:
        client = get_aws_session(AWSAccount(resource.account)).client(
            action_mapper[resource.resource_type]['service_name'],
            region_name=resource.location
        )
        try:
            action_status, extra_info = func_action(client, resource)
            Enforcement.create(resource.account.account_name, resource.id, action, datetime.now(), extra_info)
        except Exception as ex:
            action_status = ActionStatus.FAILED
            logger.error('Failed to apply action {} to {}: {}'.format(action, resource.id, ex))
        finally:
            auditlog(
                event='{}.{}.{}.{}'.format(action_issuer, resource.resource_type, action, action_status),
                actor=action_issuer,
                data={
                    'resource_id': resource.id,
                    'account_name': resource.account.account_name,
                    'location': resource.location,
                    'info': extra_info
                }
            )
            return action_status
    else:
        logger.error('Failed to apply action {} to {}: Not supported'.format(action, resource.id))
        return ActionStatus.FAILED


def stop_ec2_instance(client, resource):
    """Stop an EC2 Instance

    This function will attempt to stop a running instance.

    Args:
        client (:obj:`boto3.session.Session.client`): A boto3 client object
        resource (:obj:`Resource`): The resource object to stop

    Returns:
        `ActionStatus`
    """
    instance = EC2Instance.get(resource.id)
    if instance.state in ('stopped', 'terminated'):
        return ActionStatus.IGNORED, {}

    client.stop_instances(InstanceIds=[resource.id])
    return ActionStatus.SUCCEED, {'instance_type': resource.instance_type, 'public_ip': resource.public_ip}


def terminate_ec2_instance(client, resource):
    """Terminate an EC2 Instance

    This function will terminate an EC2 Instance.

    Args:
        client (:obj:`boto3.session.Session.client`): A boto3 client object
        resource (:obj:`Resource`): The resource object to terminate

    Returns:
        `ActionStatus`
    """
    # TODO: Implement disabling of TerminationProtection
    instance = EC2Instance.get(resource.id)
    if instance.state == 'terminated':
        return ActionStatus.IGNORED, {}
    client.terminate_instances(InstanceIds=[resource.id])
    return ActionStatus.SUCCEED, {'instance_type': resource.instance_type, 'public_ip': resource.public_ip}


def stop_s3_bucket(client, resource):
    """
    Stop an S3 bucket from being used

    This function will try to
        1. Add lifecycle policy to make sure objects inside it will expire
        2. Block certain access to the bucket
    """

    bucket_policy = {
        'Version': '2012-10-17',
        'Id': 'PutObjPolicy',
        'Statement': [
            {
                'Sid': 'cinqDenyObjectUploads',
                'Effect': 'Deny',
                'Principal': '*',
                'Action': ['s3:PutObject', 's3:GetObject'],
                'Resource': 'arn:aws:s3:::{}/*'.format(resource.id)
            }
        ]
    }

    s3_removal_lifecycle_policy = {
        'Rules': [
            {'Status': 'Enabled',
             'NoncurrentVersionExpiration': {u'NoncurrentDays': 1},
             'Filter': {u'Prefix': ''},
             'Expiration': {
                 u'Date': datetime.utcnow().replace(
                     hour=0, minute=0, second=0, microsecond=0
                 ) + timedelta(days=dbconfig.get('lifecycle_expiration_days', NS_AUDITOR_REQUIRED_TAGS, 3))
             },
             'AbortIncompleteMultipartUpload': {u'DaysAfterInitiation': 3},
             'ID': 'cloudInquisitor'}
        ]
    }

    policy_exists = s3_removal_policy_exists(client, resource)
    lifecycle_policy_exists = s3_removal_lifecycle_policy_exists(client, resource)
    if policy_exists and lifecycle_policy_exists:
        return ActionStatus.IGNORED, {}

    if not policy_exists:
        client.put_bucket_policy(Bucket=resource.id, Policy=json.dumps(bucket_policy))
        logger.info('Added policy to prevent putObject in s3 bucket {} in {}'.format(
            resource.id,
            resource.account.account_name
        ))

    if not lifecycle_policy_exists:
        # Grab S3 Metrics before lifecycle policies start removing objects

        client.put_bucket_lifecycle_configuration(
            Bucket=resource.id,
            LifecycleConfiguration=s3_removal_lifecycle_policy
        )
        logger.info('Added policy to delete bucket contents in s3 bucket {} in {}'.format(
            resource.id,
            resource.account.account_name
        ))

    return ActionStatus.SUCCEED, resource.metrics()


def delete_s3_bucket(client, resource):
    """Delete an S3 bucket

    This function will try to delete an S3 bucket

    Args:
        client (:obj:`boto3.session.Session.client`): A boto3 client object
        resource (:obj:`Resource`): The resource object to terminate

    Returns:
        `ActionStatus`
    """

    if dbconfig.get('enable_delete_s3_buckets', NS_AUDITOR_REQUIRED_TAGS, False):
        client.delete_bucket(Bucket=resource.id)
    return ActionStatus.SUCCEED, resource.metrics()


def stop_rds_instance(client, resource):
    operate_rds_instance(client, resource, 'stop')


def terminate_rds_instance(client, resource):
    operate_rds_instance(client, resource, 'terminate')


def operate_rds_instance(client, resource, action):
    resource_info = {
        'platform': 'AWS',
        'accountId': resource.account.account_id,
        'accountName': resource.account.account_name,
        'action': action,
        'region': resource.location,
        'resourceId': resource.id,
        'resourceType': 'rds',
        'resourceSubType': resource.engine
    }

    try:
        response = client.invoke(
            FunctionName=dbconfig.get('action_taker_arn', NS_AUDITOR_REQUIRED_TAGS, ''),
            Payload=json.dumps(resource_info).encode('utf-8')
        )

        if response.get('success'):
            return ActionStatus.SUCCEED, resource.metrics()
        else:
            failure_message = response.get('message')

            if response['data']['actionTaken'] == 'ignored':
                return ActionStatus.IGNORED, {'message': failure_message}
            else:
                return ActionStatus.FAILED, {'message': failure_message}
    except Exception as ex:
        return AuditActions.IGNORE, {'message': ex}


action_mapper = {
    'aws_ec2_instance': {
        'service_name': 'ec2',
        AuditActions.STOP: stop_ec2_instance,
        AuditActions.REMOVE: terminate_ec2_instance
    },
    'aws_s3_bucket': {
        'service_name': 's3',
        AuditActions.STOP: stop_s3_bucket,
        AuditActions.REMOVE: delete_s3_bucket
    },
    'aws_rds_instance': {
        'service_name': 'lambda',
        AuditActions.STOP: stop_rds_instance,
        AuditActions.REMOVE: terminate_rds_instance
    }
}
