import re

import cloud_inquisitor
import cloud_inquisitor.utils
import cloud_inquisitor.wrappers
import pytest
from tests.libs.exceptions import TestSetupError
from tests.libs.util_mocks import __check_auth, get_mocked_session, send_notification
from tests.service import *


def patch_cinq_func():
    setattr(cloud_inquisitor, 'get_aws_session', get_mocked_session)
    setattr(cloud_inquisitor, 'get_local_aws_session', get_mocked_session)
    setattr(cloud_inquisitor.utils, 'send_notification', send_notification)
    setattr(cloud_inquisitor.wrappers.check_auth, '__check_auth', __check_auth)


def pre_test_checks():
    s = re.match('^mysql://.+/(.+)?$', cloud_inquisitor.app_config.database_uri, re.IGNORECASE)
    if not s:
        raise TestSetupError('Cannot locate Database URI in the app config!')
    if not cloud_inquisitor.app_config.test_mode:
        raise TestSetupError('Test mode not enabled!')


@pytest.fixture()
def cinq_test_service():
    cts = CinqTestService()
    cts.setup()

    yield cts

    cts.shut_down()


pre_test_checks()
patch_cinq_func()
