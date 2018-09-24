from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.constants import NS_CINQ_TEST
from tests.libs.cinq_test_cls import MockRequiredTagsAuditor
from tests.libs.lib_cinq_auditor_aws_required_tags import prep_s3_testing, IGNORE_TAGSET
from tests.libs.util_cinq import setup_test_aws, aws_get_client, collect_resources


def test_collect_only(cinq_test_service):
    """
    Test if the auditor respects "collect_only" config item
    """

    # Prep
    setup_info = setup_test_aws(cinq_test_service)
    account = setup_info['account']

    prep_s3_testing(cinq_test_service, collect_only=True)

    # Add resources
    client = aws_get_client('s3')
    bucket_name = dbconfig.get('test_bucket_name', NS_CINQ_TEST, default='testbucket')
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
    assert not auditor._cinq_test_notices


def test_ignore_tag(cinq_test_service):
    """
    Test if the auditor respects "collect_only" config item
    """

    # Prep
    setup_info = setup_test_aws(cinq_test_service)
    account = setup_info['account']

    prep_s3_testing(cinq_test_service)

    # Add resources
    client = aws_get_client('s3')
    bucket_name = dbconfig.get('test_bucket_name', NS_CINQ_TEST, default='testbucket')
    client.create_bucket(Bucket=bucket_name)

    client.put_bucket_tagging(
        Bucket=bucket_name,
        Tagging={'TagSet': IGNORE_TAGSET}
    )

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
    assert not auditor._cinq_test_notices
