import logging
import re
from collections import defaultdict

import boto3.session
import requests
from pkg_resources import iter_entry_points
from werkzeug.local import LocalProxy

from cloud_inquisitor.constants import PLUGIN_NAMESPACES
from cloud_inquisitor.utils import get_user_data_configuration, read_config

logger = logging.getLogger(__name__)
__regions = None

# Setup app wide variables
config_path, app_config = LocalProxy(read_config)


def get_local_aws_session():
    """Returns a session for the local instance, not for a remote account

    Returns:
        :obj:`boto3:boto3.session.Session`
    """
    if not all((app_config.aws_api.access_key, app_config.aws_api.secret_key)):
        return boto3.session.Session()
    else:
        # If we are not running on an EC2 instance, assume the instance role
        # first, then assume the remote role
        session_args = [app_config.aws_api.access_key, app_config.aws_api.secret_key]
        if app_config.aws_api.session_token:
            session_args.append(app_config.aws_api.session_token)

        return boto3.session.Session(*session_args)


def get_aws_session(account):
    """Function to return a boto3 Session based on the account passed in the first argument.

    Args:
        account (:obj:`Account`): Account to create the session object for

    Returns:
        :obj:`boto3:boto3.session.Session`
    """
    from cloud_inquisitor.config import dbconfig

    # If no keys are on supplied for the account, use sts.assume_role instead
    session = get_local_aws_session()
    if session.get_credentials().method == 'iam-role':
        sts = session.client('sts')
    else:
        # If we are not running on an EC2 instance, assume the instance role
        # first, then assume the remote role
        temp_sts = session.client('sts')

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


# Check if the user has opted to use userdata based configuration for DB, and load it if needed
if app_config.use_user_data:
    get_user_data_configuration()

AWS_REGIONS = LocalProxy(get_aws_regions)

# Load all the plugin entry points, but don't load them just yet
CINQ_PLUGINS = defaultdict(dict)
for name, ns in PLUGIN_NAMESPACES.items():
    CINQ_PLUGINS[ns] = {
        'name': name,
        'plugins': []
    }

    for ep in iter_entry_points(ns):
        CINQ_PLUGINS[ns]['plugins'].append(ep)
