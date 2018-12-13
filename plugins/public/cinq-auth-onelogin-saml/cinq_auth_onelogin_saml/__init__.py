import json
import re
from http import HTTPStatus
from urllib.parse import urlparse

from cloud_inquisitor.config import ConfigOption
from cloud_inquisitor.constants import ROLE_USER
from cloud_inquisitor.database import db
from cloud_inquisitor.plugins import BaseAuthPlugin
from cloud_inquisitor.plugins.views import BaseView
from cloud_inquisitor.schema import User, Role
from cloud_inquisitor.utils import get_template, generate_csrf_token, generate_jwt_token
from flask import request, redirect, session
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils

NAMESPACE = 'auth_saml'


class BaseSamlRequest(BaseView):
    name = 'OneLoginSAML'
    ns = NAMESPACE
    req = None
    auth = None

    def __init__(self):
        self.req = self._prepare_flask_request()
        self.auth = self._init_saml_request()

        super(BaseSamlRequest, self).__init__()

    def _init_saml_request(self):
        tmpl = get_template('saml_settings.json')
        config = tmpl.render(
            strict=str(self.dbconfig.get('strict', self.ns, True)).lower(),
            debug=str(self.dbconfig.get('debug', self.ns, False)).lower(),
            sp_entity_id=self.dbconfig.get('sp_entity_id', self.ns),
            sp_acs=self.dbconfig.get('sp_acs', self.ns),
            sp_sls=self.dbconfig.get('sp_sls', self.ns),
            idp_entity_id=self.dbconfig.get('idp_entity_id', self.ns),
            idp_ssos=self.dbconfig.get('idp_ssos', self.ns),
            idp_sls=self.dbconfig.get('idp_sls', self.ns),
            idp_x509cert=self.dbconfig.get('idp_x509cert', self.ns)
        )

        auth = OneLogin_Saml2_Auth(self.req, json.loads(config))
        auth.set_strict(False)
        return auth

    @staticmethod
    def _prepare_flask_request():
        # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
        url_data = urlparse(request.url)
        port = url_data.port or (443 if request.scheme == 'https' else 80)

        return {
            'https': 'on' if request.scheme == 'https' else 'off',
            'http_host': request.host,
            'server_port': port,
            'script_name': request.path,
            'get_data': request.args.copy(),
            'post_data': request.form.copy()
        }


class SamlLoginRequest(BaseSamlRequest):
    URLS = ['/saml/login', '/auth/saml/login']

    def get(self):
        return redirect(self.auth.login())


class SamlLoginConsumer(BaseSamlRequest):
    URLS = ['/saml/login/consumer', '/auth/saml/login/consumer']

    def post(self):
        try:
            self.auth.process_response()
            errors = self.auth.get_errors()

            if len(errors) == 0:
                user = db.User.find_one(
                    User.username == self.auth.get_nameid(),
                    User.auth_system == self.name
                )

                if not user:
                    user_role = db.Role.find_one(Role.name == ROLE_USER)
                    user = User()
                    user.username = self.auth.get_nameid()
                    user.auth_system = self.name
                    db.session.add(user)
                    db.session.commit()
                    db.session.refresh(user)
                    User.add_role(user, [user_role])

                    self.log.debug('Added new SAML based user {}'.format(user.username))

                # Setup the user session with all the information required
                session['user'] = user
                session['samlNameId'] = user.username
                session['samlSessionIndex'] = self.auth.get_session_index()
                session['csrf_token'] = generate_csrf_token()
                session['accounts'] = [x.account_id for x in db.Account.all() if x.user_has_access(user)]

                # Redirect to the page we came from, as long as its not from one of the auth-systems
                if 'RelayState' in request.form:
                    self_url = OneLogin_Saml2_Utils.get_self_url(self.req)
                    if not re.match('{}/(auth|saml)'.format(self_url), request.form['RelayState']):
                        return redirect(self.auth.redirect_to(request.form['RelayState']))

                if 'redirectTo' in session:
                    redir = session['redirectTo']
                    del session['redirectTo']
                else:
                    redir = ''

                token = generate_jwt_token(user, self.name, saml={
                    'name_id': user.username,
                    'session_index': self.auth.get_session_index()
                })

                return redirect('/authenticate/{0}/{1}?redirectTo={2}'.format(
                    token,
                    session['csrf_token'],
                    redir
                ))
            else:
                self.log.error('Errors while logging in user: {}'.format(', '.join(errors)))
                return self.make_response(
                    {'message': 'An error occured processing user login'}, HTTPStatus.INTERNAL_SERVER_ERROR
                )

        except Exception:
            self.log.exception('Error while processing AD login')
            return self.make_response({'message': 'Internal error'}, HTTPStatus.INTERNAL_SERVER_ERROR)


class SamlLogoutRequest(BaseSamlRequest):
    URLS = ['/saml/logout', '/auth/saml/logout']

    def get(self):
        name_id = session_index = None

        if 'samlNameId' in session:
            name_id = session['samlNameId']

        if 'samlSessionIndex' in session:
            session_index = session['samlSessionIndex']

        return redirect(self.auth.logout(name_id=name_id, session_index=session_index))


class SamlLogoutConsumer(BaseSamlRequest):
    URLS = ['/saml/logout/consumer', '/auth/saml/logout/consumer']

    def get(self):
        def dscb():
            session.clear()

        url = self.auth.process_slo(delete_session_cb=dscb)
        errors = self.auth.get_errors()

        if len(errors) == 0:
            if url:
                return self.auth.redirect_to(url)

        return redirect('/logout')


class OneLoginSAMLAuth(BaseAuthPlugin):
    name = 'OneLoginSAML'
    ns = NAMESPACE
    views = (SamlLoginRequest, SamlLoginConsumer, SamlLogoutRequest, SamlLogoutConsumer)
    options = (
        ConfigOption('strict', True, 'bool', 'Strict validation of SAML responses'),
        ConfigOption('debug', False, 'bool', 'Enable SAML debug mode'),
        ConfigOption('sp_entity_id', None, 'string', 'Service Provider Entity ID'),
        ConfigOption('sp_acs', None, 'string', 'Assertion Consumer endpoint'),
        ConfigOption('sp_sls', None, 'string', 'Single Logout Service endpoint'),
        ConfigOption('idp_entity_id', None, 'string', 'Identity Provider Entity ID'),
        ConfigOption('idp_ssos', None, 'string', 'Single Sign-On Service endpoint'),
        ConfigOption('idp_sls', None, 'string', 'Single Logout Service endpoint'),
        ConfigOption('idp_x509cert', None, 'string', 'Base64 encoded x509 certificate for SAML validation')
    )
    readonly = True
    login = {'url': '/auth/saml/login'}
    logout = '/auth/saml/logout'
