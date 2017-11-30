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
import sys
from base64 import b64decode
from datetime import datetime, timedelta
from gzip import zlib

import boto3.session
import requests
from flask import Flask, request, session, abort
from flask_compress import Compress
from flask_restful import Api
from flask_script import Server
from flask_sqlalchemy import SQLAlchemy
from pkg_resources import iter_entry_points
from sqlalchemy.exc import SQLAlchemyError

from cloud_inquisitor.utils import parse_date

# Setup app wide variables
AWS_REGIONS = []
app = Flask(__name__)
Compress(app)
app.config.from_envvar('INQUISITOR_SETTINGS')
api_access_key = app.config.get('AWS_API_ACCESS_KEY')
api_secret_key = app.config.get('AWS_API_SECRET_KEY')
api_role = app.config.get('AWS_API_INSTANCE_ROLE_ARN')

if app.config.get('USE_USER_DATA', True):
    kms_region = app.config.get('KMS_REGION', 'us-west-2')
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

    user_data_url = app.config.get('USER_DATA_URL')
    res = requests.get(user_data_url)

    if res.status_code == 200:
        data = kms.decrypt(CiphertextBlob=b64decode(res.content))
        kms_config = json.loads(zlib.decompress(data['Plaintext']).decode('utf-8'))

        app.config['SQLALCHEMY_DATABASE_URI'] = kms_config['db_uri']
    else:
        print(res.status_code)
        raise RuntimeError('Failed loading user-data, cannot continue')

db = SQLAlchemy(app)
api = Api(app)

# Must be imported after we initialized the db instance

from cloud_inquisitor.config import dbconfig, DBConfig, DBCChoice
from cloud_inquisitor.constants import ROLE_ADMIN, ROLE_USER, NS_AUTH
from cloud_inquisitor.plugins.views import BaseView, LoginRedirectView, LogoutRedirectView
from cloud_inquisitor.json_utils import InquisitorJSONDecoder, InquisitorJSONEncoder
from cloud_inquisitor.schema import Account

logger = logging.getLogger(__name__)


class ServerWrapper(Server):
    """Wrapper class for the built-in runserver functionality, which registers views before calling Flask's
    ServerWrapper
    """
    def __call__(self, *args, **kwargs):
        register_views()
        super().__call__(*args, **kwargs)


def __reload_db_config():
    """Helper function to reload the DBConfig object

    Returns:
        `None`
    """
    dbconfig.reload_data()
    logger.info('Reloaded DBConfig')


def __register_auth_system(auth_system):
    """Register a given authentication system with the framework. Returns `True` if the `auth_system` is registered
    as the active auth system, else `False`

    Args:
        auth_system (:obj:`BaseAuthPlugin`): A subclass of the `BaseAuthPlugin` class to register

    Returns:
        `bool`
    """
    auth_system_settings = dbconfig.get('auth_system')

    if auth_system.name not in auth_system_settings['available']:
        auth_system_settings['available'].append(auth_system.name)
        dbconfig.set('default', 'auth_system', DBCChoice(auth_system_settings))

    if auth_system.name == auth_system_settings['enabled'][0]:
        app.active_auth_system = auth_system
        auth_system().bootstrap()
        logger.debug('Registered {} as the active auth system'.format(auth_system.name))
        return True

    else:
        logger.debug('Not trying to load the {} auth system as it is disabled by config'.format(auth_system.name))
        return False


def register_views():
    """Iterates all entry points for views and auth systems and dynamically load and register the routes with Flask

    Returns:
        `None`
    """

    api.add_resource(LoginRedirectView, '/auth/login')
    api.add_resource(LogoutRedirectView, '/auth/logout')

    for ep in iter_entry_points('cloud_inquisitor.plugins.auth'):
        cls = ep.load()
        app.available_auth_systems[cls.name] = cls

        if app.register_auth_system(cls):
            for vcls in cls.views:
                api.add_resource(vcls, *vcls.URLS)
                logger.debug('Registered auth system view {} for paths: {}'.format(
                    cls.__name__,
                    ', '.join(vcls.URLS)
                ))

    if not app.active_auth_system:
        logger.error('No auth systems active, please enable an auth system and then start the system again')
        sys.exit(-1)

    for ep in iter_entry_points('cloud_inquisitor.plugins.views'):
        view = ep.load()
        api.add_resource(view, *view.URLS)
        for itm in view.MENU_ITEMS:
            if itm.group in app.menu_items:
                app.menu_items[itm.group]['items'].append(itm)
            else:
                logger.warning('Tried registering menu item to unknown group {}'.format(itm.group))

        logger.debug('Registered view {} for paths: {}'.format(view.__name__, ', '.join(view.URLS)))


def register_types():
    """Iterates all entry points for resource types and registers a `resource_type_id` to class mapping

    Returns:
        `dict`
    """
    # FIXME: Local import to avoid app startup failures
    try:
        from cloud_inquisitor.schema import ResourceType

        types = {}
        for ep in iter_entry_points('cloud_inquisitor.plugins.types'):
            cls = ep.load()
            types[ResourceType.get(cls.resource_type).resource_type_id] = cls
            logger.debug('Registered resource type {}'.format(cls.__name__))

        return types
    except SQLAlchemyError:
        return []


@app.before_request
def before_request():
    """Checks to ensure that the session is valid and validates the users CSRF token is present

    Returns:
        `None`
    """
    if not request.path.startswith('/saml') and not request.path.startswith('/auth'):
        # Validate the session has the items we need
        if 'accounts' not in session:
            logger.debug('Missing \'accounts\' from session object, sending user to login page')
            return BaseView.make_unauth_response()

        # Require the CSRF token to be present if we are performing a change action (add, delete or modify objects)
        # but exclude the SAML endpoints from the CSRF check
        if request.method in ('POST', 'PUT', 'DELETE',):
            if session['csrf_token'] != request.headers.get('X-Csrf-Token'):
                logger.info('CSRF Token is missing or incorrect, sending user to login page')
                abort(403)


@app.after_request
def after_request(response):
    """Modifies the response object prior to sending it to the client. Used to add CORS headers to the request

    Args:
        response (response): Flask response object

    Returns:
        `None`
    """
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


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
    region_file = os.path.join(app.config.get('BASE_CFG_PATH'), 'aws_regions.json')
    if os.path.exists(region_file) and os.path.getsize(region_file) > 0:
        data = json.load(open(region_file, 'r'))
        if data['regions'] and parse_date(data['created']) > datetime.now() - timedelta(weeks=1):
            return data['regions']

    data = requests.get('https://ip-ranges.amazonaws.com/ip-ranges.json').json()
    rgx = re.compile(dbconfig.get('ignored_aws_regions_regexp', default=''), re.I)
    regions = sorted(list(set(
        x['region'] for x in data['prefixes'] if not rgx.search(x['region'])
    )))
    json.dump({'created': datetime.now().isoformat(), 'regions': regions}, open(region_file, 'w'))

    return regions

app.active_auth_system = None
app.available_auth_systems = {}
app.types = register_types()

app.register_auth_system = __register_auth_system
app.json_encoder = InquisitorJSONEncoder
app.json_decoder = InquisitorJSONDecoder

app.menu_items = {
    'default': {
        'order': 10,
        'name': None,
        'required_role': ROLE_USER,
        'items': []
    },
    'browse': {
        'order': 20,
        'name': 'Browse',
        'required_role': ROLE_USER,
        'items': []
    },
    'reports': {
        'order': 30,
        'name': 'Reports',
        'required_role': ROLE_USER,
        'items': []
    },
    'admin': {
        'order': 99,
        'name': 'Admin',
        'required_role': ROLE_ADMIN,
        'items': []
    }
}

try:
    AWS_REGIONS = get_aws_regions()
except:
    raise Exception('Unable to load list of regions from AWS API')
