import subprocess
import time

from cloud_inquisitor.config import dbconfig, apply_config
from cloud_inquisitor.constants import NS_CINQ_TEST
from cloud_inquisitor.database import db
from cloud_inquisitor.plugins.views.accounts import add_account
from cloud_inquisitor.schema import ConfigItem, Issue, Resource, ResourceProperty, Account
from tests.libs.util_mocks import service_lut
from tests.libs.var_const import CINQ_TEST_ACCOUNT_NAME, CINQ_TEST_ACCOUNT_NO

AVAILABLE_SERVICES = ['ec2', 's3', 'route53']


class CinqTestService(object):
    def __init__(self):
        self.default_dbconfig = [ns.to_json() for ns in db.ConfigNamespace.find()]
        self.add_account = add_account

        self.test_account = None

        self.scheduler = None
        self.api_server = None
        self.servers = {}
        for service in service_lut.keys():
            self.servers[service] = None

    ''' Service related routines '''

    def setup(self):
        """
        Act as the setup function before calling each test_xxx()
        """
        self.reset_db_config()
        self.reset_db_data()
        self.start_mocking_services()

    def shut_down(self):
        """
        Act as the teardown function after calling each test_xxx()

        Note that if setup() threw an exception, this function won't be called
        """
        self.stop_mocking_services()
        self.reset_db_data()
        self.reset_db_config()

    @staticmethod
    def start_mocking_service(service, port):
        if service in AVAILABLE_SERVICES:
            return subprocess.Popen(
                ['moto_server', service, '-p{}'.format(port)]
            )

    def start_mocking_services(self):
        for service in self.servers.keys():
            _, port = service_lut[service].split(':')
            self.servers[service] = self.start_mocking_service(service, port)

    def stop_mocking_service(self, service_name):
        if self.servers[service_name]:
            self.servers[service_name].kill()
            self.servers[service_name] = None

    def stop_mocking_services(self):
        for service in self.servers.keys():
            self.stop_mocking_service(service)

    ''' DB related routines '''

    @staticmethod
    def set_test_user_role(role):
        dbconfig.set(NS_CINQ_TEST, 'user_role', role)

    def reset_db_accounts(self):
        db.session.query(Account).delete()
        self.test_account = add_account(
            account_name=CINQ_TEST_ACCOUNT_NAME,
            account_number=CINQ_TEST_ACCOUNT_NO,
            account_contacts=[{'type': 'email', 'value': dbconfig.get('test_email', NS_CINQ_TEST)}],
            is_enabled=1,
            auto_commit=False
        )
        db.session.commit()

    @staticmethod
    def reset_db_issues():
        db.session.query(Issue).delete()
        db.commit()

    @staticmethod
    def reset_db_resources():
        db.session.query(Resource).delete()
        db.commit()

    def reset_db_data(self):
        self.reset_db_issues()
        self.reset_db_resources()
        self.reset_db_accounts()

    def reset_db_config(self):
        db.session.query(ConfigItem).delete()
        apply_config(self.default_dbconfig)
        db.session.commit()

    @staticmethod
    def apply_config(config):
        apply_config(config)

    @staticmethod
    def has_resource(resource_id):
        return bool(db.session.query(Resource).filter(Resource.resource_id == resource_id))

    @staticmethod
    def get_resource(resource_id):
        try:
            qry = db.session.query(Resource).filter(Resource.resource_id == resource_id).first()
            return qry[0]
        except IndexError:
            return None

    @staticmethod
    def modify_resource(resource_id, resource_property, value):
        try:
            resource = db.ResourceProperty.filter(
                ResourceProperty.resource_id == resource_id, ResourceProperty.name == resource_property
            ).first()
            if not resource:
                return False
            else:
                resource.value = value
                db.session.commit()
                return True
        finally:
            db.session.rollback()

    ''' Cinq related routines '''

    def start_scheduler(self):
        self.stop_scheduler()
        self.scheduler = subprocess.Popen(['cloud-inquisitor', 'scheduler'])

    def stop_scheduler(self):
        if self.scheduler:
            self.scheduler.kill()
            self.scheduler = None

    def start_api_server(self):
        self.stop_api_server()
        self.api_server = subprocess.Popen(['cloud-inquisitor', 'runserver'])

    def stop_api_server(self):
        if self.api_server:
            self.api_server.kill()
            self.api_server = None

    ''' Util routines '''

    @staticmethod
    def verify(verify_function, timeout, *args, **kwargs):
        time_start = time.time()

        while time.time() - time_start < timeout:
            if verify_function(*args, **kwargs):
                return True
            time.sleep(1)

        return False
