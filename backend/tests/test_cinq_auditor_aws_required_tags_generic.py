from cloud_inquisitor.config import dbconfig, DBCJSON
from cloud_inquisitor.constants import NS_AUDITOR_REQUIRED_TAGS, AuditActions, NS_CINQ_TEST
from tests.libs.cinq_test_cls import MockRequiredTagsAuditor
from tests.libs.util_cinq import setup_test_aws, aws_get_client, collect_resources


def case_1(cinq_test_service, account, recipient):
    """
    Test if the auditor respects "collect_only" config item
    """
    db_setting = dbconfig.get('audit_scope', NS_AUDITOR_REQUIRED_TAGS)
    db_setting['enabled'] = ['aws_s3_bucket']
    dbconfig.set(NS_AUDITOR_REQUIRED_TAGS, 'audit_scope', DBCJSON(db_setting))
    dbconfig.set(NS_AUDITOR_REQUIRED_TAGS, 'collect_only', True)

    bucket_name = dbconfig.get('test_bucket_name', NS_CINQ_TEST, default='testbucket')

    # Add resources
    client = aws_get_client('s3')
    client.create_bucket(Bucket=bucket_name)

    # Collect resources
    collect_resources(account=account, resource_types=['s3'])

    # Initialize auditor
    auditor = MockRequiredTagsAuditor()

    # Setup test
    cinq_test_service.modify_resource(
        bucket_name,
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
    notices = auditor._cinq_test_notices

    ''' Check if the action is correct'''
    assert notices[recipient]['not_fixed'][0]['action'] == AuditActions.REMOVE

    ''' Check if the bucket is still there '''
    assert client.list_buckets()['Buckets'][0]['Name'] == bucket_name


def test_audit(cinq_test_service):
    """

    :return:
    """

    # Prep
    cinq_test_service.start_mocking_services('s3')

    setup_info = setup_test_aws(cinq_test_service)
    recipient = setup_info['recipient']
    account = setup_info['account']

    # Tests
    for single_test_case in filter(lambda x: x[0].startswith('case_'), globals().items()):
        single_test_case[1](cinq_test_service, account, recipient)
        cinq_test_service.reset_db_data()
