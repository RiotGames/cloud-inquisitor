from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from cloud_inquisitor.constants import MSG_INVALID_USER_OR_PASSWORD, ROLE_ADMIN, ROLE_USER
from cloud_inquisitor.plugins import BaseAuthPlugin, BaseView
from cloud_inquisitor.schema import Role, User
from cloud_inquisitor.utils import generate_csrf_token, generate_jwt_token, generate_password, hash_password
from flask import session, request

from cloud_inquisitor.database import db

ph = PasswordHasher()


class BaseLocalAuthView(BaseView):
    name = 'Local Authentication'
    ns = 'auth_local'


class LocalAuthLogin(BaseLocalAuthView):
    URLS = ['/auth/local/login']

    def post(self):
        self.reqparse.add_argument('username', type=str, required=True)
        self.reqparse.add_argument('password', type=str, required=True)
        args = self.reqparse.parse_args()

        try:
            user = db.User.filter(
                User.username == args['username'],
                User.auth_system == self.name
            ).first()

            if not user:
                self.log.warn('Authentication attemp for unknown user {} from {}'.format(
                    args['username'],
                    request.remote_addr
                ))
                return self.make_response({
                    'message': MSG_INVALID_USER_OR_PASSWORD
                }, 400)

            ph.verify(user.password, args['password'])

            # Setup the user session with all the information required
            session['user'] = user
            session['csrf_token'] = generate_csrf_token()
            session['accounts'] = [x.account_id for x in db.Account.all() if x.user_has_access(user)]

            token = generate_jwt_token(user, self.name)

            return self.make_response({
                'authToken': token,
                'csrfToken': session['csrf_token']
            }, 200)

        except VerificationError:
            self.log.warn('Failed verifying password for {} from {}'.format(
                args['username'],
                request.remote_addr
            ))
            return self.make_response({
                'message': MSG_INVALID_USER_OR_PASSWORD
            }, 400)

        except Exception as ex:
            self.log.exception('Unknown error occured while attempting to login user {} from {}: {}'.format(
                args['username'],
                request.remote_addr,
                ex
            ))

        finally:
            db.session.rollback()


class LocalAuthLogout(BaseLocalAuthView):
    URLS = ['/auth/local/logout']

    def get(self):
        pass


class LocalAuth(BaseAuthPlugin):
    name = 'Local Authentication'
    ns = 'auth_local'
    views = (LocalAuthLogin, LocalAuthLogout)
    readonly = False
    login = {'state': 'auth.login'}
    logout = '/auth/local/logout'

    def bootstrap(self):
        admin_user = db.User.find_one(
            User.username == 'admin',
            User.auth_system == self.name
        )

        if not admin_user:
            roles = db.Role.filter(Role.name.in_((ROLE_ADMIN, ROLE_USER))).all()
            admin_password = generate_password()
            admin_user = User()

            admin_user.username = 'admin'
            admin_user.auth_system = self.name
            admin_user.password = hash_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            db.session.refresh(admin_user)
            User.add_role(admin_user, roles)

            self.log.error('Created admin account for local authentication, username: admin, password: {}'.format(
                admin_password
            ))

        else:
            self.log.debug('Local Auth admin user already exists, skipping')
