"""Module containing constants for use througout the application
"""
import os
import re
from collections import namedtuple
from enum import Enum

from munch import munchify

ConfigOption = namedtuple('ConfigOption', ('name', 'default_value', 'type', 'description'))

# region Plugin namespaces
PLUGIN_NAMESPACES = munchify({
    'auditor': 'cloud_inquisitor.plugins.auditors',
    'auth': 'cloud_inquisitor.plugins.auth',
    'collector': 'cloud_inquisitor.plugins.collectors',
    'commands': 'cloud_inquisitor.plugins.commands',
    'notifier': 'cloud_inquisitor.plugins.notifiers',
    'schedulers': 'cloud_inquisitor.plugins.schedulers',
    'types': 'cloud_inquisitor.plugins.types',
    'accounts': 'cloud_inquisitor.plugins.types.accounts',
    'view': 'cloud_inquisitor.plugins.views'
})
# endregion

# region Namespaces
# Auditors
NS_AUDITOR_CLOUDTRAIL = 'auditor_cloudtrail'
NS_AUDITOR_DOMAIN_HIJACKING = 'auditor_domain_hijack'
NS_AUDITOR_EBS = 'auditor_ebs'
NS_AUDITOR_IAM = 'auditor_iam'
NS_AUDITOR_REQUIRED_TAGS = 'auditor_rfc26'
NS_AUDITOR_VPC_FLOW_LOGS = 'auditor_vpc_flow_logs'


class AuditActions:
    ALERT = 'ALERT'
    FIXED = 'FIXED'
    IGNORE = 'IGNORE'
    REMOVE = 'REMOVE'
    STOP = 'STOP'


# Collectors
NS_COLLECTOR_EC2 = 'collector_ec2'

# Miscellaneous
NS_API = 'api'
NS_CINQ_TEST = 'cinq_test'
NS_EMAIL = 'email'
NS_LOG = 'log'
NS_SLACK = 'slack'
NS_GOOGLE_ANALYTICS = 'google_analytics'
NS_SCHEDULER = 'scheduler'
NS_SCHEDULER_SQS = 'scheduler_sqs'

# Authentication
NS_AUTH = 'auth'
NS_AUTH_ONELOGIN_SAML = 'saml'
# endregion

# region Regular Expressions
RGX_BUCKET = re.compile('(?P<bucket>.*?)\.s3(-website-(?P<region>.*?))?\.amazonaws.com')
RGX_BUCKET_WEBSITE = re.compile('^s3-website-(?P<region>.*?)?\.amazonaws.com')
RGX_EMAIL_VALIDATION_PATTERN = r'([a-zA-Z0-9._%+-]+[^+]@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
RGX_INSTANCE = re.compile(r'^i-(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{17})$', re.IGNORECASE)
RGX_INSTANCE_DNS = re.compile('ec2-(\d+)-(\d+)-(\d+)-(\d+)\.(?:.*\.compute|compute-\d)\.amazonaws.com')
RGX_IP = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', re.IGNORECASE)
RGX_TAG = re.compile(r'^(?P<type>tag|ip|instance):(?P<value>.*)$', re.IGNORECASE)
RGX_PROPERTY = re.compile(r'^(?P<type>property):(?P<value>.*)$', re.IGNORECASE)
# endregion

# region Built-in roles
ROLE_ADMIN = 'Admin'
ROLE_NOC = 'NOC'
ROLE_USER = 'User'
# endregion

# region General variables
UNAUTH_MESSAGE = 'Unauthorized, please log in'
MSG_INVALID_USER_OR_PASSWORD = 'Invalid user or password provided'
# endregion

# region Default app settings
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
        'session_token': None,
    },

    'database_uri': 'mysql://cinq:secretpass@localhost:3306/inquisitor',

    'flask': {
        'secret_key': 'verysecretkey',
        'json_sort_keys': False,
    }
}

DEFAULT_MENU_ITEMS = {
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

DEFAULT_CONFIG_OPTIONS = [
    {
        'prefix': 'default',
        'name': 'Default',
        'sort_order': 0,
        'options': [
            ConfigOption('debug', False, 'bool', 'Enable debug mode for flask'),
            ConfigOption('session_expire_time', 43200, 'int', 'Time in seconds before sessions expire'),
            ConfigOption('role_name', 'cinq_role', 'string',
                         'Role name Cloud Inquisitor will use in each account'),
            ConfigOption('ignored_aws_regions_regexp', '(^cn-|GLOBAL|-gov)', 'string',
                         'A regular expression used to filter out regions from the AWS static data'),
            ConfigOption(
                name='auth_system',
                default_value={
                    'enabled': ['Local Authentication'],
                    'available': ['Local Authentication'],
                    'max_items': 1,
                    'min_items': 1
                },
                type='choice',
                description='Enabled authentication module'
            ),
            ConfigOption('scheduler', 'StandaloneScheduler', 'string', 'Default scheduler module'),
            ConfigOption('jwt_key_file_path', 'ssl/private.key', 'string',
                         'Path to the private key used to encrypt JWT session tokens. Can be relative to the '
                         'folder containing the configuration file, or absolute path')
        ],
    },
    {
        'prefix': 'log',
        'name': 'Logging',
        'sort_order': 1,
        'options': [
            ConfigOption('log_level', 'INFO', 'string', 'Log level'),
            ConfigOption('enable_syslog_forwarding', False, 'bool',
                         'Enable forwarding logs to remote log collector'),
            ConfigOption('remote_syslog_server_addr', '127.0.0.1', 'string',
                         'Address of the remote log collector'),
            ConfigOption('remote_syslog_server_port', 514, 'string', 'Port of the remote log collector'),
            ConfigOption('log_keep_days', 31, 'int', 'Delete log entries older than n days'),
        ],
    },
    {
        'prefix': 'api',
        'name': 'API',
        'sort_order': 2,
        'options': [
            ConfigOption('host', '127.0.0.1', 'string', 'Host of the API server'),
            ConfigOption('port', 5000, 'int', 'Port of the API server'),
            ConfigOption('workers', 6, 'int', 'Number of worker processes spawned for the API')
        ]
    },
    {
        'prefix': 'cinq_test',
        'name': 'Tests',
        'sort_order': 3,
        'options': [
            ConfigOption('test_email', '', 'string', 'Email used for testing and getting emails'),
            ConfigOption('user_role', ROLE_ADMIN, 'string', 'Role used for testing')
        ]
    }
]
# endregion


# HTTP Response codes
class HTTP(object):
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    SERVER_ERROR = 500
    UNAVAILABLE = 503


class EBSIssueState(Enum):
    COMPLIANT = 0
    DETECTED = 1
    ALERT_3WEEKS = 2
    ALERT_4WEEKS = 3
    SHUTDOWN_READY = 4
    SHUTDOWN = 5
    TERMINATE = 6
    DELETED = 7
    IGNORED = 8


class SchedulerStatus(object):
    PENDING = 0
    STARTED = 1
    COMPLETED = 2
    ABORTED = 8
    FAILED = 9


class AccountTypes(object):
    AWS = 'AWS'
    DNS_AXFR = 'DNS_AXFR'
    DNS_CLOUDFLARE = 'DNS_CLOUDFLARE'
