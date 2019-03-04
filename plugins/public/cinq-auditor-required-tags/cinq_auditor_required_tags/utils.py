import json

from botocore.exceptions import ClientError


def s3_removal_policy_exists(client, resource):
    try:
        for policy in json.loads(client.get_bucket_policy(Bucket=resource.id)['Policy'])['Statement']:
            if policy.get('Sid', '') == 'cinqDenyObjectUploads':
                return True
        return False
    except ClientError as error:
        if error.response['Error']['Code'] == 'NoSuchBucketPolicy':
            return False


def s3_removal_lifecycle_policy_exists(client, resource):
    try:
        rules = client.get_bucket_lifecycle_configuration(Bucket=resource.id)['Rules']
        for rule in rules:
            if rule['ID'] == 'cloudInquisitor':
                return True
        return False
    except (ClientError, KeyError):
        return False
