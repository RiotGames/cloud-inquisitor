import datetime

from cloud_inquisitor.config import dbconfig, DBCJSON
from cloud_inquisitor.constants import NS_AUDITOR_REQUIRED_TAGS, AuditActions, NS_CINQ_TEST
from tests.libs.cinq_test_cls import MockRequiredTagsAuditor
from tests.libs.lib_cinq_auditor_aws_required_tags import s3_upload_file_from_string
from tests.libs.util_cinq import setup_test_aws, aws_get_client, collect_resources


def case_1(cinq_test_service, account, recipient):
    """
    Test will pass if for an S3 bucket meet the following condition:
        - Bucket is empty
        - No Bucket Policy was set
        - No Lifecycle Policy was set
        - No tag was set

    The Auditor will:
        - Detect non-compliant S3 buckets
        - Respect grace period settings
        - Be able to remove an empty bucket successfully when the "REMOVE" criteria are met
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
    Test will pass if for an S3 bucket meet the following condition:
        - Bucket is NOT empty
        - No Bucket Policy was set
        - No Lifecycle Policy was set
        - No tag was set

    The Auditor will:
        - Apply Cinq lifecycle policy to the bucket
    """
    # Add resources
    client = aws_get_client('s3')
    bucket_name = dbconfig.get('test_bucket_name', NS_CINQ_TEST, default='testbucket')
    client.create_bucket(Bucket=bucket_name)
    resource = client.list_buckets()['Buckets'][0]
    s3_upload_file_from_string(client, bucket_name, 'sample', 'sample text')

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
    current_policy = client.get_bucket_lifecycle_configuration(Bucket=bucket_name)['Rules'][0]
    assert current_policy['ID'] == 'cloudInquisitor'
    assert current_policy['Status'] == 'Enabled'
    assert current_policy['Expiration'] == {'Days': dbconfig.get('grace_period', NS_AUDITOR_REQUIRED_TAGS, 4)}


def case_3(cinq_test_service, account, recipient):
    """
    Test will pass if for an S3 bucket meet the following condition:
        - Bucket is empty
        - No Bucket Policy was set
        - No Lifecycle Policy was set
        - There was no tag doing the initial audit but missing tags were added during the second audit

    The Auditor will:
        - Detect non-compliant S3 buckets during the first audit
        - Detect Fixed Buckets correctly
    """
    client = aws_get_client('s3')
    bucket_name = dbconfig.get('test_bucket_name', NS_CINQ_TEST, default='testbucket')
    client.create_bucket(Bucket=bucket_name)
    resource = client.list_buckets()['Buckets'][0]

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

    notices = auditor._cinq_test_notices
    assert notices[recipient]['not_fixed'][0]['resource']['resource_id'] == bucket_name

    tagset = [{'Key': x, 'Value': 'value@example.com'} for x in dbconfig.get('required_tags', NS_AUDITOR_REQUIRED_TAGS, [])]
    client.put_bucket_tagging(
        Bucket=bucket_name,
        Tagging={'TagSet': tagset}
    )
    collect_resources(account=account, resource_types=['s3'])
    auditor.run()
    notices = auditor._cinq_test_notices

    # Verify if the auditor will report the issue fixed
    assert notices[recipient]['fixed'][0]['action'] == AuditActions.FIXED
    assert notices[recipient]['fixed'][0]['resource'].resource_id == bucket_name


def case_4(cinq_test_service, account, recipient):
    """
    Test will pass if for an S3 bucket meet the following condition:
        - Is compliant

    The Auditor will:
        - Not mark compliant buckets as non-compliant
    """
    client = aws_get_client('s3')
    bucket_name = dbconfig.get('test_bucket_name', NS_CINQ_TEST, default='testbucket')
    client.create_bucket(Bucket=bucket_name)
    resource = client.list_buckets()['Buckets'][0]

    tagset = [{'Key': x, 'Value': 'value@example.com'} for x in
              dbconfig.get('required_tags', NS_AUDITOR_REQUIRED_TAGS, [])]
    client.put_bucket_tagging(
        Bucket=bucket_name,
        Tagging={'TagSet': tagset}
    )

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
    assert auditor._cinq_test_notices == {}


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
    for single_test_case in filter(lambda x: x[0].startswith('case_'), globals().items()):
        single_test_case[1](cinq_test_service, account, recipient)
        cinq_test_service.reset_db_data()
