import subprocess
import time

from cloud_inquisitor.config import dbconfig, apply_config
from cloud_inquisitor.constants import NS_CINQ_TEST
from cloud_inquisitor.database import db
from cloud_inquisitor.plugins.views.accounts import add_account
from cloud_inquisitor.schema import ConfigItem, Issue, Resource, ResourceProperty, Account
from tests.libs.util_mocks import service_lut
from tests.libs.var_const import CINQ_TEST_ACCOUNT_NAME, CINQ_TEST_ACCOUNT_NO


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

    def shut_down(self):
        """
        Act as the teardown function after calling each test_xxx()

        Note that if setup() threw an exception, this function won't be called
        """
        self.stop_mocking_services()
        self.reset_db_data()
        self.reset_db_config()

    def start_mocking_service(self, service, port):
        if service in service_lut.keys():
            if self.servers[service]:
                self.stop_mocking_service(service)
            self.servers[service] = subprocess.Popen(['moto_server', service, '-p{}'.format(port)])

    def start_mocking_services(self, *args):
        """
        Start mocking services

        Args:
            args (`list`): a list of mocking services you want to start. Note that the name of the services should be in
                             AVAILABLE_SERVICES. Otherwise nothing will happen. If it is empty, all services in
                             AVAILABLE_SERVICES will be started
        """
        if not args:
            args = service_lut.keys()

        for service in args:
            _, port = service_lut[service].split(':')
            self.start_mocking_service(service, port)

    def stop_mocking_service(self, service_name):
        if service_name in service_lut.keys() and self.servers[service_name]:
            self.servers[service_name].kill()
            self.servers[service_name] = None

    def stop_mocking_services(self, *args):
        """
        Stop mocking services

        Args:
            args (`list`): a list of mocking services you want to stop. Note that the name of the services should be in
                             AVAILABLE_SERVICES. Otherwise nothing will happen. If it is empty, all services will be
                             stopped
        """
        if not args:
            args = service_lut.keys()

        for service in args:
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
