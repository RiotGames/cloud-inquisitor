from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.constants import NS_CINQ_TEST
from cloud_inquisitor.utils import NotificationContact
from tests.libs.cinq_test_cls import MockEBSAuditor
from tests.libs.util_cinq import aws_get_client, collect_resources
from tests.libs.var_const import CINQ_TEST_ACCOUNT_NAME, CINQ_TEST_ACCOUNT_NO


def test_audit(cinq_test_service):
    """

    :return:
    """

    # Prep
    recipient = NotificationContact('email', dbconfig.get('test_email', NS_CINQ_TEST))
    cinq_test_service.start_mocking_services('ec2')
    account = cinq_test_service.add_test_account(
        account_type='AWS',
        account_name=CINQ_TEST_ACCOUNT_NAME,
        contacts=[{'type': 'email', 'value': dbconfig.get('test_email', NS_CINQ_TEST)}],
        properties={
            'account_number': CINQ_TEST_ACCOUNT_NO
        }
    )

    # Add resources
    client = aws_get_client('ec2')
    resource = client.create_volume(
        AvailabilityZone=client.describe_availability_zones()['AvailabilityZones'][0]['ZoneName'],
        Size=16
    )

    # Collect resources
    collect_resources(account=account, resource_types=['ec2'])

    # Start auditor
    auditor = MockEBSAuditor()

    # Test 1 --- Test if the auditor can catch the volume we added
    auditor.run()
    notice = auditor._cinq_test_notices

    assert notice[recipient][0].volume_id.value == resource['VolumeId']

    # TODO: More tests
