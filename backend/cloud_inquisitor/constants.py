"""Module containing constants for use througout the application
"""
import re
from enum import Enum

from munch import munchify


# region Plugin namespaces
PLUGIN_NAMESPACES = munchify({
    'auditor': ['cloud_inquisitor.plugins.auditors'],
    'auth': ['cloud_inquisitor.plugins.auth'],
    'collector': ['cloud_inquisitor.plugins.collectors'],
    'notifier': ['cloud_inquisitor.plugins.notifiers'],
    'schedulers': ['cloud_inquisitor.plugins.schedulers'],
    'types': ['cloud_inquisitor.plugins.types'],
    'view': ['cloud_inquisitor.plugins.views']
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

# Collectors
NS_COLLECTOR_EC2 = 'collector_ec2'

# Miscellaneous
NS_API = 'api'
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
RGX_EMAIL_VALIDATION_PATTERN = r'([A-Z0-9._%+-]+[^+]@[A-Z0-9.-]+\.[A-Z]{2,})'
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
