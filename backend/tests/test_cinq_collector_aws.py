from tests.libs.util_cinq import aws_get_client, collect_resources, setup_test_aws


def test_collect(cinq_test_service):
    """

    :return:
    """

    # Prep
    setup_info = setup_test_aws(cinq_test_service)
    account = setup_info['account']

    cinq_test_service.start_mocking_services('ec2')

    # Add resources
    client = aws_get_client('ec2')
    resource = client.run_instances(ImageId='i-10000', MinCount=1, MaxCount=1)

    # Start collector
    collect_resources(account=account, resource_types=['ec2'])

    # verify
    assert cinq_test_service.has_resource('non-exist-id') is False
    assert cinq_test_service.has_resource(resource['Instances'][0]['InstanceId']) is True

    cinq_test_service.stop_mocking_services('ec2')
