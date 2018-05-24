import subprocess

from cloud_inquisitor.config import dbconfig, apply_config
from cloud_inquisitor.constants import NS_CINQ_TEST
from cloud_inquisitor.database import db
from cloud_inquisitor.schema import ConfigItem, Issue, Account, Resource
from tests.libs.exceptions import TestSetupError
from tests.libs.util_db import empty_tables, has_resource, get_resource, modify_resource
from tests.libs.util_misc import verify
from tests.libs.util_mocks import service_lut
from tests.libs.var_const import CINQ_TEST_ACCOUNT_NAME, CINQ_TEST_ACCOUNT_NO


class CinqTestService(object):
    def __init__(self):
        self.default_dbconfig = [ns.to_json() for ns in db.ConfigNamespace.find()]

        self.test_account = None

        self.scheduler = None
        self.api_server = None
        self.servers = {}
        for service in service_lut.keys():
            self.servers[service] = None

        self.empty_tables = empty_tables
        self.has_resource = has_resource
        self.get_resource = get_resource
        self.modify_resource = modify_resource
        self.verify = verify

    ''' Service related routines '''

    def setup(self):
        """
        Act as the setup function before calling each test_xxx()
        """
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
            args (`list`): a list of mocking services you want to start. Note that the name of the services should be
                             supported by moto. Raises TestSetupError if empty or invalid inputs were given
        """
        if not args:
            raise TestSetupError('Need to specify at least 1 service to start')

        services = []
        for service in args:
            if service not in service_lut:
                raise TestSetupError('Mocking the following service is not supported: {}'.format(service))

            services.append((service, service_lut[service].split(':')[-1]))

        for service, port in services:
            self.start_mocking_service(service, port)

    def stop_mocking_service(self, service_name):
        if service_name in service_lut.keys() and self.servers[service_name]:
            self.servers[service_name].kill()
            self.servers[service_name] = None

    def stop_mocking_services(self, *args):
        """
        Stop mocking services

        Args:
            args (`list`): a list of mocking services you want to stop. If it is empty, all services will be stopped
        """
        if not args:
            args = service_lut.keys()

        for service in args:
            self.stop_mocking_service(service)

    ''' DB related routines '''

    def add_test_account(self, required_roles=None, **kwargs):
        self.test_account = Account(**kwargs)
        self.test_account.required_roles = required_roles if required_roles else []

        db.session.add(self.test_account)
        db.session.commit()

    def reset_db_data(self):
        empty_tables(Account, Issue, Resource)
        self.add_test_account(
            name=CINQ_TEST_ACCOUNT_NAME,
            account_number=CINQ_TEST_ACCOUNT_NO,
            contacts=[{'type': 'email', 'value': dbconfig.get('test_email', NS_CINQ_TEST)}],
            enabled=True,
            ad_group_base=None
        )

    def reset_db_config(self):
        empty_tables(ConfigItem)
        apply_config(self.default_dbconfig)

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
