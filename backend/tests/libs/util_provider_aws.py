from cloud_inquisitor import get_aws_session


def get_aws_regions(service):
    return get_aws_session().get_available_regions(service)
