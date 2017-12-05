import binascii
import hashlib
import json
import os
import random
import re
import string
import time
import pkg_resources
from datetime import datetime

import jwt
import requests
from argon2 import PasswordHasher
from dateutil import parser
from jinja2 import Environment, FileSystemLoader

from cloud_inquisitor.constants import RGX_EMAIL_VALIDATION_PATTERN, RGX_BUCKET, ROLE_ADMIN

__jwt_data = None


class MenuItem(object):
    def __init__(self, group=None, name=None, state=None, active=None, section=None, args=None, order=100):
        self.group = group
        self.name = name
        self.state = state
        self.active = active
        self.section = section
        self.args = args or {}
        self.order = order

    def to_json(self):
        return {
            'group': self.group,
            'name': self.name,
            'state': self.state,
            'active': self.active,
            'section': self.section,
            'args': self.args or {},
            'order': self.order
        }


def get_hash(data):
    """Return the SHA256 hash of an object

    >>> get_hash('my-test-string')
    '56426297313df008f6ac9d4554b0724a2b3d39a7134bf2d9aede21ec680dd9c4'

    Args:
        data: Object to hash

    Returns:
        SHA256 hash of the object
    """
    return hashlib.sha256(str(data).encode('utf-8')).hexdigest()


def is_truthy(value, default=False):
    """Evaluate a value for truthiness

    >>> is_truthy('Yes')
    True
    >>> is_truthy('False')
    False
    >>> is_truthy(1)
    True

    Args:
        value (Any): Value to evaluate
        default (bool): Optional default value, if the input does not match the true or false values

    Returns:
        True if a truthy value is passed, else False
    """

    if value is None:
        return False

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value > 0

    trues = ('1', 'true', 'y', 'yes', 'ok')
    falses = ('', '0', 'false', 'n', 'none', 'no')

    if value.lower().strip() in falses:
        return False

    elif value.lower().strip() in trues:
        return True

    else:
        if default:
            return default
        else:
            raise ValueError('Invalid argument given to truthy: {0}'.format(value))


def validate_email(email, partial_match=False):
    """Perform email address validation

    >>> validate_email('akjaer@riotgames.com')
    True
    >>> validate_email('Asbjorn Kjaer <akjaer@riotgames.com')
    False
    >>> validate_email('Asbjorn Kjaer <akjaer@riotgames.com', partial_match=True)
    True

    Args:
        email (str): Email address to match
        partial_match (bool): If False (default), the entire string must be a valid email address. If true, any valid
         email address in the string will trigger a valid response

    Returns:
        True if the value contains an email address, else False
    """
    rgx = re.compile(RGX_EMAIL_VALIDATION_PATTERN, re.I)
    if partial_match:
        return rgx.search(email) is not None
    else:
        return rgx.match(email) is not None


def get_template(template):
    """Return a Jinja2 template by filename

    Args:
        template (str): Name of the template to return

    Returns:
        A Jinja2 Template object
    """
    tmplpath = os.path.join(pkg_resources.resource_filename('cloud_inquisitor', 'data'), 'templates')
    tmplenv = Environment(loader=FileSystemLoader(tmplpath), autoescape=True)
    tmplenv.filters['json_loads'] = json.loads
    tmplenv.filters['slack_quote_join'] = lambda data: ", ".join(list('`{}`'.format(x) for x in data))

    return tmplenv.get_template(template)


def parse_bucket_info(domain):
    """Parse a domain name to gather the bucket name and region for an S3 bucket. Returns a tuple
     (bucket_name, bucket_region) if a valid domain name, else `None`

     >>> parse_bucket_info('www.riotgames.com.br.s3-website-us-west-2.amazonaws.com')
    ('www.riotgames.com.br', 'us-west-2')

    Args:
        domain (`str`): Domain name to parse

    Returns:
        :obj:`list` of `str`: `str`,`None`
    """
    match = RGX_BUCKET.match(domain)
    if match:
        data = match.groupdict()
        return data['bucket'], data['region'] or 'us-east-1'


def to_utc_date(date):
    """Convert a datetime object from local to UTC format

    >>> import datetime
    >>> d = datetime.datetime(2017, 8, 15, 18, 24, 31)
    >>> to_utc_date(d)
    datetime.datetime(2017, 8, 16, 1, 24, 31)

    Args:
        date (`datetime`): Input datetime object

    Returns:
        `datetime`
    """
    return datetime.utcfromtimestamp(float(date.strftime('%s'))).replace(tzinfo=None) if date else None


def isoformat(date):
    """Convert a datetime object to a ISO 8601 formatted string, with added None type handling

    >>> import datetime
    >>> d = datetime.datetime(2017, 8, 15, 18, 24, 31)
    >>> isoformat(d)
    '2017-08-15T18:24:31'

    Args:
        date (`datetime`): Input datetime object

    Returns:
        `str`
    """
    return date.isoformat() if date else None


def generate_password(length=32):
    """Generate a cryptographically secure random string to use for passwords

    Args:
        length (int): Length of password, defaults to 32 characters

    Returns:
        Randomly generated string
    """
    return ''.join(random.SystemRandom().choice(string.ascii_letters + '!@#$+.,') for _ in range(length))


def generate_csrf_token():
    """Return a randomly generated string for use as CSRF Tokens

    Returns:
        `str`
    """
    return binascii.hexlify(os.urandom(32)).decode()


def hash_password(password):
    """Return an argon2 hashed version of the password provided

        password: Password to hash

    Returns:
        String representing the hashed password
    """
    return PasswordHasher().hash(password)


def generate_jwt_token(user, authsys, **kwargs):
    """Generate a new JWT token, with optional extra information. Any data provided in `**kwargs`
    will be added into the token object for auth specific usage

    Args:
        user (:obj:`User`): User object to generate token for
        authsys (str): The auth system for which the token was generated
        **kwargs (dict): Any optional items to add to the token

    Returns:
        Encoded JWT token
    """
    # Local import to prevent app startup failures
    from cloud_inquisitor.config import dbconfig

    token = {
        'auth_system': authsys,
        'exp': time.time() + dbconfig.get('session_expire_time'),
        'roles': [role.name for role in user.roles]
    }

    if kwargs:
        token.update(**kwargs)

    enc = jwt.encode(token, get_jwt_key_data(), algorithm='HS512')
    return enc.decode()

def get_jwt_key_data():
    """Returns the data for the JWT private key used for encrypting the user login token as a string object

    Returns:
        `str`
    """
    global __jwt_data

    if __jwt_data:
        return __jwt_data

    from cloud_inquisitor import app
    from cloud_inquisitor.config import dbconfig

    jwt_key_file = dbconfig.get('jwt_key_file_path', default='ssl/private.key')
    if not os.path.isabs(jwt_key_file):
        jwt_key_file = os.path.join(app.config.get('BASE_CFG_PATH'), jwt_key_file)

    with open(os.path.join(jwt_key_file), 'r') as f:
        __jwt_data = f.read()

    return __jwt_data


def has_access(user, required_roles, match_all=True):
    """Check if the user meets the role requirements. If mode is set to AND, all the provided roles must apply

    Args:
        user (:obj:`User`): User object
        required_roles (`list` of `str`): List of roles that the user must have applied
        match_all (`bool`): If true, all the required_roles must be applied to the user, else any one match will
         return `True`

    Returns:
        `bool`
    """
    # Admins have access to everything
    if ROLE_ADMIN in user.roles:
        return True

    if isinstance(required_roles, str):
        if required_roles in user.roles:
            return True

        return False

    # If we received a list of roles to match against
    if match_all:
        for role in required_roles:
            if role not in user.roles:
                return False

        return True

    else:
        for role in required_roles:
            if role in user.roles:
                return True

        return False


def merge_lists(*args, sort=False):
    """Merge an arbitrary number of lists into a single list and dedupe it

    >>> merge_lists(('foo', 'bar'), ('bar', 'foobar'))
    ['foobar', 'foo', 'bar']
    >>> merge_lists(('foo', 'bar'), ('bar', 'foobar'), sort=True)
    ['bar', 'foo', 'foobar']

    Args:
        *args: Two or more lists
        sort (bool): Sort the merged list before returning it, default: `False`

    Returns:
        A deduped merged list of all the provided lists as a single list
    """

    out = set()
    for lst in filter(None, args):
        out.update(lst)

    return sorted(out) if sort else list(out)


def to_camelcase(inStr):
    """Converts a string from snake_case to camelCase

    >>> to_camelcase('convert_to_camel_case')
    'convertToCamelCase'

    Args:
        inStr (str): String to convert

    Returns:
        String formatted as camelCase
    """
    return re.sub('_([a-z])', lambda x: x.group(1).upper(), inStr)


def from_camelcase(inStr):
    """Converts a string from camelCase to snake_case

    >>> from_camelcase('convertToPythonicCase')
    'convert_to_pythonic_case'

    Args:
        inStr (str): String to convert

    Returns:
        String formatted as snake_case
    """
    return re.sub('[A-Z]', lambda x: '_' + x.group(0).lower(), inStr)


def get_resource_id(prefix, *data):
    """Returns a unique ID based on the SHA256 hash of the provided data. Each element in `*data` must support
    the __str__ method

    >>> get_resource_id('ec2', 'lots', 'of', 'data')
    'ec2-00607742acfcbb63'

    Args:
        prefix (`str`): Key prefix
        *data (`list`): List of items to use to build the resource id

    Returns:
        `str`
    """
    return '{}-{}'.format(
        prefix,
        get_hash("-".join(str(x) for x in data))[-16:]
    )


def parse_date(date_string):
    """Parse a string as a date. If the string fails to parse, `None` will be returned instead

    >>> parse_date('2017-08-15T18:24:31')
    datetime.datetime(2017, 8, 15, 18, 24, 31)

    Args:
        date_string (`str`): Date in string format to parse

    Returns:
        `datetime`, `None`
    """
    try:
        return parser.parse(date_string)
    except TypeError:
        return None
