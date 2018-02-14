import json
import logging
import os
import re
from datetime import datetime, timedelta

import boto3.session
import munch
import requests
from werkzeug.local import LocalProxy

from cloud_inquisitor.constants import CONFIG_FILE_PATHS, DEFAULT_CONFIG
from cloud_inquisitor.utils import get_user_data_configuration, parse_date

logger = logging.getLogger(__name__)

def read_config():
    """Attempts to read the application configuration file and will raise a `FileNotFoundError` if the
    configuration file is not found. Returns the folder where the configuration file was loaded from, and
    a `Munch` (dict-like object) containing the configuration

    Configuration file paths searched, in order:
        * ~/.cinq/config.json'
        * ./config.json
        * /usr/local/etc/cloud-inquisitor/config.json

    Returns:
        `str`, `dict` -
    """
    config = munch.munchify(DEFAULT_CONFIG)

    for fpath in CONFIG_FILE_PATHS:
        if os.path.exists(fpath):
            config.update(json.load(open(fpath, 'r')))
            return os.path.dirname(fpath), config

    raise FileNotFoundError('Configuration file not found')

# Setup app wide variables
config_path, app_config = LocalProxy(read_config)

# Check if the user has opted to use UserData based configuration for DB, and load it if needed
if app_config.use_user_data:
    get_user_data_configuration(app_config)


def get_aws_session(account):
    """Function to return a boto3 Session based on the account passed in the first argument.

    Args:
        account (:obj:`Account`): Account to create the session object for

    Returns:
        :obj:`boto3:boto3.session.Session`
    """
    from cloud_inquisitor.dbconfig import dbconfig

    # If no keys are on supplied for the account, use sts.assume_role instead
    if not app_config.aws_api.access_key or not app_config.aws_api.secret_key:
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


def get_aws_regions():
    """Load a list of AWS regions from the AWS static data.

    Returns:
        :obj:`list` of `str`
    """
    from cloud_inquisitor.config import dbconfig

    data = requests.get('https://ip-ranges.amazonaws.com/ip-ranges.json').json()
    rgx = re.compile(dbconfig.get('ignored_aws_regions_regexp', default='(^cn-|GLOBAL|-gov)'), re.I)
    regions = sorted(list(set(
        x['region'] for x in data['prefixes'] if not rgx.search(x['region'])
    )))

    return regions

try:
    AWS_REGIONS = get_aws_regions()
except:
    raise Exception('Unable to load list of regions from AWS API')
