from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.constants import NS_CINQ_TEST
from cloud_inquisitor.utils import NotificationContact
from tests.libs.cinq_test_cls import MockEBSAuditor
from tests.libs.util_cinq import run_aws_collector, aws_get_client


def test_audit(cinq_test_service):
    """

    :return:
    """

    # Prep
    recipient = NotificationContact('email', dbconfig.get('test_email', NS_CINQ_TEST))
    cinq_test_service.start_mocking_services('ec2')

    # Add resources
    client = aws_get_client('ec2')
    resource = client.create_volume(
        AvailabilityZone=client.describe_availability_zones()['AvailabilityZones'][0]['ZoneName'],
        Size=16
    )

    # Collect resource
    run_aws_collector(cinq_test_service.test_account)

    # Start auditor
    auditor = MockEBSAuditor()

    # Test 1 --- Test if the auditor can catch the volume we added
    auditor.run()
    notice = auditor._cinq_test_notices

    assert notice[recipient]['issues'][0].volume_id.value == resource['VolumeId']

    # TODO: More tests
