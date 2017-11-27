from .. import test_cinq  # MUST BE FIRST to load FLASK CONTEXT

from cloud_inquisitor.constants import UNAUTH_MESSAGE, MSG_INVALID_USER_OR_PASSWORD


class BuiltinTestCase(test_cinq.CinqTestCase):
    def test_unauthorized(self):
        response = self.anon_client.get('/')
        assert response.status_code == 401

    def test_authorized(self):
        response = self.admin_client.get('/',
                                         headers={
                                             'X-Csrf-Token': 'bypass_csrf',
                                             'Authorization': self.admin_jwt
                                         })
        assert response.status_code == 404

    def test_builtin_unauthorized(self):
        response = self.anon_client.post('/auth/builtin/login',
                                         data=dict(
                                             username='nobody',
                                             password='whatever'
                                         ))
        assert MSG_INVALID_USER_OR_PASSWORD.encode() in response.data

    def test_ebs_view_anon(self):
        response = self.anon_client.get('/api/v1/ebs')
        assert UNAUTH_MESSAGE.encode() in response.data
