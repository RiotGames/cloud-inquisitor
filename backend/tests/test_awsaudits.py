from cloud_inquisitor import app
from cloud_inquisitor.schema import Role, User
from cloud_inquisitor.utils import generate_jwt_token

import unittest


class CinqTestCase(unittest.TestCase):
    anon_client = None
    admin_client = None
    admin_jwt = None

    def setUp(self):
        app.testing = True
        self.anon_client = app.test_client()

        self.admin_client = app.test_client()
        with self.admin_client.session_transaction() as admin_session:
            admin_session['user'] = self.admin_user()
            admin_session['csrf_token'] = 'bypass_csrf'
            admin_session['accounts'] = [1]
        self.additional_test_setup()

    def additional_test_setup(self):
        # Each sub-class can implement this, so it still gets setup above
        pass

    def admin_user(self):
        role = Role()
        role.role_id = 1
        role.name = 'Admin'
        user = User()
        user.username = 'admin'
        user.auth_system = 'builtin'
        user.roles = [role]
        self.admin_jwt = generate_jwt_token(user, 'builtin')
        return user
