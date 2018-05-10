from boto3 import Session
from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.constants import NS_CINQ_TEST, ROLE_ADMIN

service_lut = {
    'ami': '127.0.0.1:30000',
    'ec2': '127.0.0.1:30000',
    'kms': '127.0.0.1:30001',
    'route53': '127.0.0.1:30002',
    's3': '127.0.0.1:30003',
    'ses': '127.0.0.1:30004',
    'sts': '127.0.0.1:30005'
}


class MockSession(Session):
    def client(self, service_name, region_name=None, api_version=None,
               use_ssl=True, verify=None, endpoint_url=None,
               aws_access_key_id=None, aws_secret_access_key=None,
               aws_session_token=None, config=None):
        """
        Patch boto3.session.client so all requests will be redirected to AWS Mocking services
        """
        return super().client(
            service_name=service_name,
            region_name=region_name,
            api_version=api_version,
            use_ssl=False,
            verify=False,
            endpoint_url='http://{}'.format(service_lut[service_name]),
            aws_access_key_id='',
            aws_secret_access_key='',
            aws_session_token='',
            config=config
        )


def send_notification(*, subsystem, recipients, subject, body_html, body_text):
    pass


def __check_auth(self, view):
    test_role = dbconfig.get('test_role', NS_CINQ_TEST, ROLE_ADMIN)
    if test_role in self.role:
        return
    else:
        return view.make_unauth_response()


def no_op(*args, **kwargs):
    return


def get_mocked_session(*args, **kwargs):
    return MockSession()
