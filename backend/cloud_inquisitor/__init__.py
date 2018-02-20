import logging
import re

import boto3.session
import gevent.monkey; gevent.monkey.patch_all() # NOQA: fix for https://github.com/gevent/gevent/issues/941
import requests
from werkzeug.local import LocalProxy

from cloud_inquisitor.utils import get_user_data_configuration, read_config

logger = logging.getLogger(__name__)
__regions = None

# Setup app wide variables
config_path, app_config = LocalProxy(read_config)

# Check if the user has opted to use userdata based configuration for DB, and load it if needed
if app_config.use_user_data:
    get_user_data_configuration(app_config)


def get_aws_session(account):
    """Function to return a boto3 Session based on the account passed in the first argument.

    Args:
        account (:obj:`Account`): Account to create the session object for

    Returns:
        :obj:`boto3:boto3.session.Session`
    """
    from cloud_inquisitor.config import dbconfig

    # If no keys are on supplied for the account, use sts.assume_role instead
    if not all((app_config.aws_api.access_key, app_config.aws_api.secret_key)):
        sts = boto3.session.Session().client('sts')
    else:
        # If we are not running on an EC2 instance, assume the instance role
        # first, then assume the remote role
        temp_sts = boto3.session.Session(app_config.aws_api.access_key, app_config.aws_api.secret_key).client('sts')
        audit_sts_role = temp_sts.assume_role(
            RoleArn=app_config.aws_api.instance_role_arn,
            RoleSessionName='inquisitor'
        )
        sts = boto3.session.Session(
            audit_sts_role['Credentials']['AccessKeyId'],
            audit_sts_role['Credentials']['SecretAccessKey'],
            audit_sts_role['Credentials']['SessionToken']
        ).client('sts')

    role = sts.assume_role(
        RoleArn='arn:aws:iam::{}:role/{}'.format(
            account.account_number,
            dbconfig.get('role_name', default='cinq_role')
        ),
        RoleSessionName='inquisitor'
    )

    sess = boto3.session.Session(
        role['Credentials']['AccessKeyId'],
        role['Credentials']['SecretAccessKey'],
        role['Credentials']['SessionToken']
    )

    return sess


def get_aws_regions(*, force=False):
    """Load a list of AWS regions from the AWS static data.

    Args:
        force (`bool`): Force fetch list of regions even if we already have a cached version

    Returns:
        :obj:`list` of `str`
    """
    from cloud_inquisitor.config import dbconfig
    global __regions

    if force or not __regions:
        logger.debug('Loading list of AWS regions from static data')
        data = requests.get('https://ip-ranges.amazonaws.com/ip-ranges.json').json()
        rgx = re.compile(dbconfig.get('ignored_aws_regions_regexp', default='(^cn-|GLOBAL|-gov)'), re.I)
        __regions = sorted(list({x['region'] for x in data['prefixes'] if not rgx.search(x['region'])}))

    return __regions


AWS_REGIONS = LocalProxy(get_aws_regions)
