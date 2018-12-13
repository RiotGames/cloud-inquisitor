import logging
import json

from botocore.exceptions import ClientError
from datetime import datetime, timedelta

from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.plugins.types.accounts import AWSAccount

from cinq_auditor_required_tags.exceptions import ResourceKillError, ResourceStopError, ResourceActionError
from cloud_inquisitor import get_aws_session
from cloud_inquisitor.constants import NS_AUDITOR_REQUIRED_TAGS
from cloud_inquisitor.log import auditlog
from cloud_inquisitor.plugins.types.resources import EC2Instance
from cloud_inquisitor.plugins.types.enforcements import Enforcement

logger = logging.getLogger(__name__)


def process_action(resource, action, resource_type):
    """Process an audit action for a resource, if possible

    Args:
        resource (:obj:`Resource`): A resource object to perform the action on
        action (`str`): Type of action to perform (`kill` or `stop`)
        resource_type (`str`): Type of the resource

    Returns:
        `bool` - Returns the result from the action function
    """
    func_action = action_mapper[resource_type][action]
    if func_action:
        session = get_aws_session(AWSAccount(resource.account))
        client = session.client(
            action_mapper[resource_type]['service_name'],
            region_name=resource.location
        )
        return func_action(client, resource)

    return False


def stop_ec2_instance(client, resource):
    """Stop an EC2 Instance

    This function will attempt to stop a running instance. If the instance is already stopped the function will return
    False, else True.

    Args:
        client (:obj:`boto3.session.Session.client`): A boto3 client object
        resource (:obj:`Resource`): The resource object to stop

    Returns:
        `bool`
    """
    try:
        instance = EC2Instance.get(resource.resource_id)
        if instance.state not in ('stopped', 'terminated'):
            instance_type = "Not Found"
            public_ip = "Not Found"
            for prop in resource.properties:
                if prop.name == "instance_type":
                    instance_type = prop.value
                if prop.name == "public_ip":
                    public_ip = prop.value

            metrics = {"instance_type": instance_type, "public_ip": public_ip}

            client.stop_instances(InstanceIds=[resource.resource_id])
            logger.debug('Stopped instance {}/{}'.format(resource.account.account_name, resource.resource_id))
            Enforcement.create(resource.account_id, resource.resource_id, 'STOP',
                               datetime.now(), metrics)
            auditlog(
                event='required_tags.ec2.stop',
                actor=NS_AUDITOR_REQUIRED_TAGS,
                data={
                    'resource_id': resource.resource_id,
                    'account_name': resource.account.account_name,
                    'location': resource.location
                }
            )

            return True
        else:
            return False
    except Exception as error:
        logger.info('Failed to stop instance {}/{}: {}'.format(
            resource.account.account_name,
            resource.resource_id,
            error
        ))
        raise ResourceStopError('Failed to stop instance {}/{}: {}'.format(
            resource.account,
            resource.resource_id,
            error
        ))


def terminate_ec2_instance(client, resource):
    """Terminate an EC2 Instance

    This function will terminate an EC2 Instance. Returns `True` if succesful, or raises an exception if not

    Args:
        client (:obj:`boto3.session.Session.client`): A boto3 client object
        resource (:obj:`Resource`): The resource object to terminate

    Returns:
        `bool` - True if the instance was terminated. Will raise an exception if failed
    """
    # TODO: Implement disabling of TerminationProtection
    try:
        # Gather instance metrics before termination
        instance_type = "Not Found"
        public_ip = "Not Found"
        for prop in resource.properties:
            if prop.name == "instance_type":
                instance_type = prop.value
            if prop.name == "public_ip":
                public_ip = prop.value

        metrics = {"instance_type": instance_type, "public_ip": public_ip}

        client.terminate_instances(InstanceIds=[resource.resource_id])
        logger.info('Terminated instance {}/{}/{}'.format(
            resource.account,
            resource.location,
            resource.resource_id
        ))
        Enforcement.create(resource.account_id, resource.resource_id, 'TERMINATE',
                           datetime.now(), metrics)
        auditlog(
            event='required_tags.ec2.terminate',
            actor=NS_AUDITOR_REQUIRED_TAGS,
            data={
                'resource_id': resource.resource_id,
                'account_name': resource.account.account_name,
                'location': resource.location
            }
        )
        return True

    except Exception as error:
        logger.info('Failed to kill instance {}/{}/{}: {}'.format(
            resource.account.account_name,
            resource.location,
            resource.resource_id,
            error
        ))
        raise ResourceKillError('Failed to kill instance {}/{}/{}: {}'.format(
            resource.account.account_name,
            resource.location,
            resource.resource_id,
            error
        ))


def delete_s3_bucket(client, resource):
    try:
        session = get_aws_session(AWSAccount(resource.account))
        bucket = session.resource('s3', resource.location).Bucket(resource.resource_id)
        days_until_expiry = dbconfig.get('lifecycle_expiration_days', NS_AUDITOR_REQUIRED_TAGS, 3)
        # Separate rule for Object Markers is needed and can't be combined into a single rule per AWS API
        lifecycle_policy = {
            'Rules': [
                {'Status': 'Enabled',
                 'NoncurrentVersionExpiration': {u'NoncurrentDays': days_until_expiry},
                 'Filter': {u'Prefix': ''},
                 'Expiration': {
                     'Date': datetime.utcnow().replace(
                         hour=0, minute=0, second=0, microsecond=0
                     ) + timedelta(days=days_until_expiry)
                 },
                 'AbortIncompleteMultipartUpload': {u'DaysAfterInitiation': days_until_expiry},
                 'ID': 'cinqRemoveObjectsAndVersions'},

                {'Status': 'Enabled',
                 'Filter': {u'Prefix': ''},
                 'Expiration': {
                     'ExpiredObjectDeleteMarker': True
                 },
                 'ID': 'cinqRemoveDeletedExpiredMarkers'}
            ]
        }

        bucket_policy = {
            'Version': '2012-10-17',
            'Id': 'PutObjPolicy',
            'Statement': [
                {'Sid': 'cinqDenyObjectUploads',
                 'Effect': 'Deny',
                 'Principal': '*',
                 'Action': ['s3:PutObject', 's3:GetObject'],
                 'Resource': 'arn:aws:s3:::{}/*'.format(resource.resource_id)
                 }
            ]
        }

        metrics = {'Unavailable': 'Unavailable'}
        for prop in resource.properties:
            if prop.name == "metrics":
                metrics = prop.value

        objects = list(bucket.objects.limit(count=1))
        versions = list(bucket.object_versions.limit(count=1))
        if not objects and not versions:
            bucket.delete()
            logger.info('Deleted s3 bucket {} in {}'.format(resource.resource_id, resource.account))
            Enforcement.create(resource.account_id, resource.resource_id, 'DELETED',
                               datetime.now(), metrics)
            auditlog(
                event='required_tags.s3.terminate',
                actor=NS_AUDITOR_REQUIRED_TAGS,
                data={
                    'resource_id': resource.resource_id,
                    'account_name': resource.account.account_name,
                    'location': resource.location
                }
            )
            return True

        else:
            try:
                rules = bucket.LifecycleConfiguration().rules
                for rule in rules:
                    if rule['ID'] == 'cinqRemoveDeletedExpiredMarkers':
                        rules_exists = True
                        break
                else:
                    rules_exists = False
            except ClientError:
                rules_exists = False

            try:
                current_bucket_policy = bucket.Policy().policy
            except ClientError as error:
                if error.response['Error']['Code'] == 'NoSuchBucketPolicy':
                    current_bucket_policy = 'missing'

            try:
                if not rules_exists:
                    # Grab S3 Metrics before lifecycle policies start removing objects

                    bucket.LifecycleConfiguration().put(LifecycleConfiguration=lifecycle_policy)
                    logger.info('Added policies to delete bucket contents in s3 bucket {} in {}'.format(
                        resource.resource_id,
                        resource.account
                    ))
                    Enforcement.create(resource.account_id, resource.resource_id, 'LIFECYCLE_APPLIED',
                                       datetime.now(), metrics)

                if 'cinqDenyObjectUploads' not in current_bucket_policy:
                    bucket.Policy().put(Policy=json.dumps(bucket_policy))
                    logger.info('Added policy to prevent putObject in s3 bucket {} in {}'.format(
                        resource.resource_id,
                        resource.account
                    ))

            except ClientError as error:
                logger.error(
                    'Problem applying the bucket policy or lifecycle configuration to bucket {} / account {} / {}'
                    .format(resource.resource_id, resource.account_id, error.response['Error']['Code']))

            if rules_exists and 'cinqDenyObjectUploads' in current_bucket_policy:
                # We're waiting for the lifecycle policy to delete data
                raise ResourceActionError({'msg': 'wait_for_deletion'})

    except ResourceActionError as error:
        raise ResourceActionError(error)
    except Exception as error:
        logger.info(
            'Failed to delete s3 bucket {} in {}, error is {}'.format(resource.resource_id, resource.account, error))

        raise ResourceKillError(
            'Failed to delete s3 bucket {} in {}. Reason: {}'.format(resource.resource_id, resource.account, error)
        )


action_mapper = {
    'aws_ec2_instance': {
        'service_name': 'ec2',
        'stop': stop_ec2_instance,
        'kill': terminate_ec2_instance
    },
    'aws_s3_bucket': {
        'service_name': 's3',
        'stop': None,
        'kill': delete_s3_bucket
    }
}
