from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.constants import NS_CINQ_TEST
from tests.libs.cinq_test_cls import MockRequiredTagsAuditor
from tests.libs.util_cinq import aws_get_client, run_aws_collector


def test_audit(cinq_test_service):
    """

    :return:
    """

    # Prep
    recipient = dbconfig.get('test_email', NS_CINQ_TEST)
    cinq_test_service.start_mocking_services('ec2')

    # Add resources
    client = aws_get_client('ec2')
    resource = client.run_instances(ImageId='i-10000', MinCount=1, MaxCount=1)

    # Collect resource
    run_aws_collector(cinq_test_service.test_account)

    # Start auditor
    auditor = MockRequiredTagsAuditor()
    auditor.run()

    # Test 1 --- Test if auditor will pick up non-compliant instances which is still in grace period
    auditor.run()
    assert auditor._cinq_test_notices == {}

    # Test 2 --- Test if auditor will pick up non-compliant instances correctly

    ''' Modify resources' property'''
    assert cinq_test_service.modify_resource(
        resource['Instances'][0]['InstanceId'],
        'launch_date',
        '2000-01-01T00:00:00'
    ) is True

    auditor.run()
    notice = auditor._cinq_test_notices

    assert recipient in notice
    assert auditor._cinq_test_notices[recipient]['issues'][0].instance_id == resource['Instances'][0]['InstanceId']
