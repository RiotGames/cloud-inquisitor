#
import os

# Setup paths
BASE_CFG_PATH = os.path.abspath(os.path.dirname(__file__))
BASE_PATH = os.path.dirname(BASE_CFG_PATH)

# Configure logging
LOG_LEVEL = 'INFO'
DEBUG = APP_DEBUG

# Gather DB settings from a KMS encrypted user-data string. See documentation for more information
USE_USER_DATA = APP_USE_USER_DATA
KMS_ACCOUNT_NAME = 'APP_KMS_ACCOUNT_NAME'
USER_DATA_URL = 'APP_USER_DATA_URL'

# AWS API key. Only required if you are not using instance profiles to allow access to the AWS API's to assume roles
AWS_API_ACCESS_KEY = 'APP_AWS_API_ACCESS_KEY'
AWS_API_SECRET_KEY = 'APP_AWS_API_SECRET_KEY'

# Instance Profile ARN (only used if using static API keys)
AWS_API_INSTANCE_ROLE_ARN = 'APP_INSTANCE_ROLE_ARN'

# Flask recret key
SECRET_KEY = 'APP_SECRET_KEY'

# Database settings. if USE_USER_DATA is enabled, these will be overwritten with the
# information from the encrypted user data string, and can be left at default values
SQLALCHEMY_DATABASE_URI = 'APP_DB_URI'
SQLALCHEMY_POOL_SIZE = 50
SQLALCHEMY_MAX_OVERFLOW = 15
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Do not sort JSON output
JSON_SORT_KEYS = False
