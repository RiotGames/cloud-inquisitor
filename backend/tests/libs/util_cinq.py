from cloud_inquisitor import get_aws_session
from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.constants import NS_CINQ_TEST
from cloud_inquisitor.utils import NotificationContact
from tests.libs.util_mocks import no_op
from tests.libs.var_const import CINQ_TEST_REGION, CINQ_TEST_ACCOUNT_NAME, CINQ_TEST_ACCOUNT_NO

from cinq_collector_aws import AWSAccountCollector, AWSRegionCollector


def aws_get_client(client_type, region=CINQ_TEST_REGION):
    return get_aws_session().client(client_type, region)


def collect_all_resources(account, region=CINQ_TEST_REGION):
    AWSRegionCollector.update_vpcs = no_op
    AWSRegionCollector.update_beanstalks = no_op
    region_collector = AWSRegionCollector(account, region)
    region_collector.run()

    AWSAccountCollector.update_cloudfront = no_op
    account_collector = AWSAccountCollector(account)
    account_collector.run()


def collect_resources(account, resource_types, region=CINQ_TEST_REGION):
    if not isinstance(resource_types, list):
        raise TypeError('resource_types needs to be a list!')

    region_collector = AWSRegionCollector(account, region)
    account_collector = AWSAccountCollector(account)

    for resource_type in resource_types:
        if resource_type == 'ec2':
            region_collector.update_instances()
            region_collector.update_volumes()
            region_collector.update_amis()
            region_collector.update_snapshots()
        elif resource_type == 'route53':
            account_collector.update_route53()
        elif resource_type == 's3':
            account_collector.update_s3buckets()


def setup_test_aws(cinq_test_service):
    recipient = NotificationContact(
        type='email',
        value=dbconfig.get('test_email', NS_CINQ_TEST)
    )
    account = cinq_test_service.add_test_account(
        account_type='AWS',
        account_name=CINQ_TEST_ACCOUNT_NAME,
        contacts=[{'type': 'email', 'value': dbconfig.get('test_email', NS_CINQ_TEST)}],
        properties={
            'account_number': CINQ_TEST_ACCOUNT_NO
        }
    )

    return {
        'account': account,
        'recipient': recipient
    }
