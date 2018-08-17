from cloud_inquisitor.config import dbconfig, DBCJSON
from cloud_inquisitor.constants import NS_AUDITOR_REQUIRED_TAGS
from tests.libs.cinq_test_cls import MockRequiredTagsAuditor
from tests.libs.util_cinq import setup_test_aws, aws_get_client, collect_resources


def case_1(cinq_test_service, account, recipient):
    bucket_name = 'testbucket'

    # Add resources
    client = aws_get_client('s3')
    client.create_bucket(Bucket=bucket_name)
    resource = client.list_buckets()['Buckets'][0]

    # Collect resources
    collect_resources(account=account, resource_types=['s3'])

    # Initialize auditor
    auditor = MockRequiredTagsAuditor()

    # Test 1 --- Test if auditor can pick up non-compliant resources correctly
    auditor.run()
    notices = auditor._cinq_test_notices

    assert resource['Name'] == notices[recipient]['not_fixed'][0]['resource']['resource_id']


def test_audit(cinq_test_service):
    """

    :return:
    """

    # Prep
    cinq_test_service.start_mocking_services('s3')

    setup_info = setup_test_aws(cinq_test_service)
    recipient = setup_info['recipient']
    account = setup_info['account']

    db_setting = dbconfig.get('audit_scope', NS_AUDITOR_REQUIRED_TAGS)
    db_setting['enabled'] = ['aws_s3_bucket']
    dbconfig.set(NS_AUDITOR_REQUIRED_TAGS, 'audit_scope', DBCJSON(db_setting))

    # Tests
    case_1(cinq_test_service, account, recipient)
