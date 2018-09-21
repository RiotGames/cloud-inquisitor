from tests.libs.util_cinq import aws_get_client, collect_resources, setup_test_aws


def case_1(cinq_test_service, account, recipient):
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


def test_collect(cinq_test_service):
    """

    :return:
    """

    # Prep
    setup_info = setup_test_aws(cinq_test_service)
    recipient = setup_info['recipient']
    account = setup_info['account']

    # Tests
    for single_test_case in filter(lambda x: x[0].startswith('case_'), globals().items()):
        single_test_case[1](cinq_test_service, account, recipient)
        cinq_test_service.reset_db_data()
