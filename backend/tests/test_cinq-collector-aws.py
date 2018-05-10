from tests.libs.util_cinq import aws_get_client, run_aws_collector


def verify_test_collect(cinq_test_service, resource):
    return cinq_test_service.has_resource(resource['Instances'][0]['InstanceId'])


def test_collect(cinq_test_service):
    """

    :return:
    """

    # Add resources
    client = aws_get_client('ec2')
    resource = client.run_instances(ImageId='i-10000', MinCount=1, MaxCount=1)

    # Start collector
    run_aws_collector(cinq_test_service.test_account)

    # verify
    assert cinq_test_service.verify(verify_test_collect, 120, cinq_test_service, resource) is True
