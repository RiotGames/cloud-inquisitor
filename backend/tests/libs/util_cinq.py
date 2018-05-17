from cloud_inquisitor import get_aws_session
from tests.libs.util_mocks import no_op
from tests.libs.var_const import CINQ_TEST_REGION

from cinq_collector_aws.region import AWSRegionCollector


def aws_get_client(client_type, region=CINQ_TEST_REGION):
    return get_aws_session().client(client_type, region)


def run_aws_collector(account, region=CINQ_TEST_REGION):
    AWSRegionCollector.update_vpcs = no_op
    AWSRegionCollector.update_beanstalks = no_op
    collector = AWSRegionCollector(account, region)
    collector.run()
