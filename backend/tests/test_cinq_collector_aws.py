from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.constants import NS_CINQ_TEST
from tests.libs.util_cinq import aws_get_client, collect_resources
from tests.libs.var_const import CINQ_TEST_ACCOUNT_NAME, CINQ_TEST_ACCOUNT_NO


def test_collect(cinq_test_service):
    """

    :return:
    """

    # Prep
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
    resource = client.run_instances(ImageId='i-10000', MinCount=1, MaxCount=1)

    # Start collector
    collect_resources(account=account, resource_types=['ec2'])

    # verify
    assert cinq_test_service.has_resource('non-exist-id') is False
    assert cinq_test_service.has_resource(resource['Instances'][0]['InstanceId']) is True
