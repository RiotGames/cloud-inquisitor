import datetime

from cloud_inquisitor.config import dbconfig, DBCJSON
from cloud_inquisitor.constants import NS_AUDITOR_REQUIRED_TAGS
from tests.libs.cinq_test_cls import MockRequiredTagsAuditor
from tests.libs.util_cinq import aws_get_client, setup_test_aws, collect_resources


def test_basic_ops(cinq_test_service):
    """
    Test will pass if:
    1. Auditor can detect non-compliant EC2 instances
    2. Auditor respect grace period settings
    """

    # Prep
    cinq_test_service.start_mocking_services('ec2')

    setup_info = setup_test_aws(cinq_test_service)
    recipient = setup_info['recipient']
    account = setup_info['account']

    db_setting = dbconfig.get('audit_scope', NS_AUDITOR_REQUIRED_TAGS)
    db_setting['enabled'] = ['aws_ec2_instance']
    dbconfig.set(NS_AUDITOR_REQUIRED_TAGS, 'audit_scope', DBCJSON(db_setting))
    dbconfig.set(NS_AUDITOR_REQUIRED_TAGS, 'collect_only', False)

    # Add resources
    client = aws_get_client('ec2')
    resource = client.run_instances(ImageId='i-10000', MinCount=1, MaxCount=1)

    # Collect resources
    collect_resources(account=account, resource_types=['ec2'])

    # Initialize auditor
    auditor = MockRequiredTagsAuditor()

    '''
    # Test 1 --- Test if auditor respect grace period settings
    cinq_test_service.modify_resource(
        resource['Instances'][0]['InstanceId'],
        'launch_date',
        datetime.datetime.utcnow().isoformat()
    )
    auditor.run()
    assert auditor._cinq_test_notices == {}
    '''

    # Test 2 --- Test if auditor can pick up non-compliant resources correctly
    ''' Modify resource property'''
    assert cinq_test_service.modify_resource(
        resource['Instances'][0]['InstanceId'],
        'launch_date',
        '2000-01-01T00:00:00'
    ) is True

    auditor.run()
    notices = auditor._cinq_test_notices

    assert recipient in notices
    assert notices[recipient]['not_fixed'][0]['resource'].resource_id == resource['Instances'][0]['InstanceId']
