"""Main entry point for the Flask app. Sets up the app, loggers and database connections

.. data:: app

    The main Flask application object

.. data:: db

    The Flask SQLAlchemy database object
"""
import json
import logging
import os
import re
from base64 import b64decode
from datetime import datetime, timedelta
from gzip import zlib

import boto3.session
import munch
import requests
from werkzeug.local import LocalProxy

from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.database import get_db_connection
from cloud_inquisitor.utils import parse_date

CONFIG_FILE_PATHS = (
    os.path.expanduser('~/.cinq/config.json'),
    os.path.join(os.getcwd(), 'config.json'),
    '/usr/local/etc/cloud-inquisitor/config.json',
)

DEFAULT_CONFIG = {
    'log_level': 'INFO',
    'use_user_data': True,
    'kms_account_name': None,
    'kms_region': 'us-west-2',
    'user_data_url': 'http://169.254.269.254/latest/user-data',

    'aws_api': {
        'access_key': None,
        'secret_key': None,
        'instance_role_arn': None,
    },

    'database_uri': 'mysql://cinq:secretpass@localhost:3306/inquisitor',

    'flask': {
        'secret_key': 'verysecretkey',
        'json_sort_keys': False,
    }
}

def read_config():
    config = munch.munchify(DEFAULT_CONFIG)

    for fpath in CONFIG_FILE_PATHS:
        if os.path.exists(fpath):
            config.update(json.load(open(fpath, 'r')))
            return os.path.dirname(fpath), config

    raise FileNotFoundError('Configuration file not found')

# Setup app wide variables
config_path, app_config = LocalProxy(read_config)
AWS_REGIONS = []

api_access_key = app_config.aws_api.access_key
api_secret_key = app_config.aws_api.secret_key
api_role = app_config.aws_api.instance_role_arn

if app_config.use_user_data:
    kms_region = app_config.kms_region

    if api_access_key and api_secret_key:
        sts = boto3.session.Session(api_access_key, api_secret_key).client('sts')
        audit_role = sts.assume_role(RoleArn=api_role, RoleSessionName='cloud_inquisitor')
        kms = boto3.session.Session(
            audit_role['Credentials']['AccessKeyId'],
            audit_role['Credentials']['SecretAccessKey'],
            audit_role['Credentials']['SessionToken'],
        ).client('kms', region_name=kms_region)
    else:
        kms = boto3.session.Session().client('kms', region_name=kms_region)

    user_data_url = app_config.user_data_url
    res = requests.get(user_data_url)

    if res.status_code == 200:
        data = kms.decrypt(CiphertextBlob=b64decode(res.content))
        kms_config = json.loads(zlib.decompress(data['Plaintext']).decode('utf-8'))

        app_config.database_uri = kms_config['db_uri']
    else:
        raise RuntimeError('Failed loading user-data, cannot continue: {}: {}'.format(res.status_code, res.content))

db = get_db_connection()


# Must be imported after we initialized the db instance
logger = logging.getLogger(__name__)


def get_aws_session(account):
    """Function to return a boto3 Session based on the account passed in the first argument.

    Args:
        account (:obj:`Account`): Account to create the session object for

    Returns:
        :obj:`boto3:boto3.session.Session`
    """
    # If no keys are on supplied for the account, use sts.assume_role instead
    if not api_access_key or not api_secret_key:
        sts = boto3.session.Session().client('sts')
    else:
        # If we are not running on an EC2 instance, assume the instance role
        # first, then assume the remote role
        temp_sts = boto3.session.Session(api_access_key, api_secret_key).client('sts')
        audit_sts_role = temp_sts.assume_role(RoleArn=api_role, RoleSessionName='inquisitor')
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
    """Load a list of AWS regions from file, provided the file exists, is not empty and is current (less than one week old). If the file
    doesn't exist or is out of date, load a new copy from the AWS static data.

    Returns:
        :obj:`list` of `str`
    """
    region_file = os.path.join(config_path, 'aws_regions.json')
    if os.path.exists(region_file) and os.path.getsize(region_file) > 0:
        data = json.load(open(region_file, 'r'))
        if data['regions'] and parse_date(data['created']) > datetime.now() - timedelta(weeks=1):
            return data['regions']

    data = requests.get('https://ip-ranges.amazonaws.com/ip-ranges.json').json()
    rgx = re.compile(dbconfig.get('ignored_aws_regions_regexp', default='(^cn-|GLOBAL|-gov)'), re.I)
    regions = sorted(list(set(
        x['region'] for x in data['prefixes'] if not rgx.search(x['region'])
    )))
    json.dump({'created': datetime.now().isoformat(), 'regions': regions}, open(region_file, 'w'))

    return regions

try:
    AWS_REGIONS = get_aws_regions()
except:
    raise Exception('Unable to load list of regions from AWS API')
