import random
import uuid

from cloud_inquisitor.config import dbconfig, DBCJSON
from cloud_inquisitor.constants import NS_AUDITOR_REQUIRED_TAGS
from tests.libs.cinq_test_cls import MockRequiredTagsAuditor
from tests.libs.lib_cinq_auditor_aws_required_tags import VALID_TAGSET, prep_s3_testing, set_audit_scope
from tests.libs.util_cinq import setup_test_aws, aws_get_client, collect_resources
from tests.libs.util_provider_aws import get_aws_regions


def test_volume_ec2_s3(cinq_test_service):
    """

    :return:
    """
    # Prep
    setup_info = setup_test_aws(cinq_test_service)
    recipient = setup_info['recipient']
    account = setup_info['account']

    set_audit_scope('aws_ec2_instance', 'aws_s3_bucket')
    dbconfig.set(NS_AUDITOR_REQUIRED_TAGS, 'collect_only', False)
    cinq_test_service.start_mocking_services('cloudwatch', 'ec2', 's3')

    num_resources = 500
    compliant_buckets = []
    non_compliant_buckets = []
    compliant_ec2 = []
    non_compliant_ec2 = []

    client_s3 = aws_get_client('s3')
    client_ec2 = aws_get_client('ec2')
    regions = get_aws_regions('s3')

    # Workaround for a moto cloudwatch KeyError bug
    regions.remove('eu-west-3')

    # Setup resources
    for i in range(0, num_resources):
        bucket_name = uuid.uuid4().hex
        client_s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': random.choice(regions)}
        )
        compliant_buckets.append(bucket_name) if random.randint(0, 1) else non_compliant_buckets.append(bucket_name)

        resource = client_ec2.run_instances(ImageId='i-{}'.format(i), MinCount=1, MaxCount=1)
        instance_id = resource['Instances'][0]['InstanceId']
        compliant_ec2.append(instance_id) if random.randint(0, 1) else non_compliant_ec2.append(instance_id)

    for instance_id in compliant_ec2:
        client_ec2.create_tags(
            Resources=[instance_id],
            Tags=VALID_TAGSET
        )

    for item in compliant_buckets:
        client_s3.put_bucket_tagging(
            Bucket=item,
            Tagging={'TagSet': VALID_TAGSET}
        )

    # collection
    collect_resources(account=account, resource_types=['ec2', 's3'])

    for item in compliant_buckets + non_compliant_buckets:
        cinq_test_service.modify_resource(
            item,
            'creation_date',
            '2000-01-01T00:00:00'
        )

    for instance_id in compliant_ec2 + non_compliant_ec2:
        cinq_test_service.modify_resource(
            instance_id,
            'launch_date',
            '2000-01-01T00:00:00'
        )

    auditor = MockRequiredTagsAuditor()
    auditor.run()

    compliant_resources = compliant_buckets + compliant_ec2
    non_compliant_resources = non_compliant_buckets + non_compliant_ec2
    for item in auditor._cinq_test_notices[recipient]['not_fixed']:
        assert item['resource'].resource_id not in compliant_resources
        assert item['resource'].resource_id in non_compliant_resources

    assert len(non_compliant_resources) == len(auditor._cinq_test_notices[recipient]['not_fixed'])
