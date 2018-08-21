import datetime

from cloud_inquisitor.config import dbconfig, DBCJSON
from cloud_inquisitor.constants import NS_AUDITOR_REQUIRED_TAGS, AuditActions, NS_CINQ_TEST
from tests.libs.cinq_test_cls import MockRequiredTagsAuditor
from tests.libs.util_cinq import setup_test_aws, aws_get_client, collect_resources


def case_1(cinq_test_service, account, recipient):
    """
    Test will pass if:
    1. Auditor can detect non-compliant S3 buckets
    2. Auditor respect grace period settings
    3. Auditor can remove an empty bucket successfully when the "REMOVE" criteria are met
    """

    bucket_name = dbconfig.get('test_bucket_name', NS_CINQ_TEST, default='testbucket')

    # Add resources
    client = aws_get_client('s3')
    client.create_bucket(Bucket=bucket_name)
    resource = client.list_buckets()['Buckets'][0]

    # Collect resources
    collect_resources(account=account, resource_types=['s3'])

    # Initialize auditor
    auditor = MockRequiredTagsAuditor()

    # Test 1 --- Test if auditor respect grace period settings
    cinq_test_service.modify_resource(
        resource['Name'],
        'creation_date',
        datetime.datetime.utcnow().isoformat()
    )
    auditor.run()
    assert auditor._cinq_test_notices == {}

    # Test 2 --- Test if auditor can pick up non-compliant resources correctly
    cinq_test_service.modify_resource(
        resource['Name'],
        'creation_date',
        '2000-01-01T00:00:00'
    )

    auditor.run()
    notices = auditor._cinq_test_notices

    assert resource['Name'] == notices[recipient]['not_fixed'][0]['resource']['resource_id']

    # Test 3 --- Modify the issue creation date so it will meet the criteria of "remove" action
    cinq_test_service.modify_issue(
        auditor._cinq_test_notices[recipient]['not_fixed'][0]['issue'].id,
        'created',
        0
    )
    auditor.run()
    notices = auditor._cinq_test_notices

    ''' Check if the action is correct'''
    assert notices[recipient]['not_fixed'][0]['action'] == AuditActions.REMOVE

    ''' Check if the bucket is actually removed '''
    assert len(client.list_buckets()['Buckets']) == 0


def case_2(cinq_test_service, account, recipient):
    """
    Test will pass if:
    1. Auditor can handle non-empty bucket when the "REMOVE" criteria are met
    """

    from io import StringIO
    file_obj = StringIO()
    file_obj.write('Test Text')

    bucket_name = dbconfig.get('test_bucket_name', NS_CINQ_TEST, default='testbucket')

    # Add resources
    client = aws_get_client('s3')
    client.create_bucket(Bucket=bucket_name)
    resource = client.list_buckets()['Buckets'][0]
    client.upload_fileobj(file_obj, bucket_name, 'sample')

    # Collect resources
    collect_resources(account=account, resource_types=['s3'])

    # Initialize auditor
    auditor = MockRequiredTagsAuditor()

    # Setup test case
    cinq_test_service.modify_resource(
        resource['Name'],
        'creation_date',
        '2000-01-01T00:00:00'
    )
    auditor.run()
    cinq_test_service.modify_issue(
        auditor._cinq_test_notices[recipient]['not_fixed'][0]['issue'].id,
        'created',
        0
    )
    auditor.run()

    # Verify if the Lifecycle policy is added
    assert client.get_bucket_lifecycle_configuration(Bucket=bucket_name)['Rules'][0]['ID'] == 'cloudInquisitor'
    assert client.get_bucket_lifecycle_configuration(Bucket=bucket_name)['Rules'][0]['Status'] == 'Enabled'
    assert client.get_bucket_lifecycle_configuration(Bucket=bucket_name)['Rules'][0]['Expiration'] == {'Days': 1}


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
    cinq_test_service.reset_db_data()
    case_2(cinq_test_service, account, recipient)
