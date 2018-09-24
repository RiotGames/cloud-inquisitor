from tests.libs.cinq_test_cls import MockEBSAuditor
from tests.libs.util_cinq import aws_get_client, collect_resources, setup_test_aws


def test_audit(cinq_test_service):
    """

    :return:
    """

    # Prep
    cinq_test_service.start_mocking_services('ec2')

    setup_info = setup_test_aws(cinq_test_service)
    recipient = setup_info['recipient']
    account = setup_info['account']

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
