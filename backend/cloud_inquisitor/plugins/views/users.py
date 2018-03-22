from flask import session, current_app

from cloud_inquisitor.constants import ROLE_ADMIN, ROLE_USER, HTTP
from cloud_inquisitor.database import db
from cloud_inquisitor.log import auditlog
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.schema import User, Role
from cloud_inquisitor.utils import MenuItem, generate_password, hash_password
from cloud_inquisitor.wrappers import check_auth, rollback


class UserList(BaseView):
    URLS = ['/api/v1/users']
    MENU_ITEMS = [
        MenuItem(
            'admin',
            'Users',
            'user.list',
            'user',
            order=3,
            args={
                'page': 1,
                'count': 50,
                'authSystem': None
            }
        )
    ]

    @rollback
    @check_auth(ROLE_ADMIN)
    def get(self):
        """List all users"""
        self.reqparse.add_argument('page', type=int, default=1, required=True)
        self.reqparse.add_argument('count', type=int, default=50, choices=[25, 50, 100])
        self.reqparse.add_argument('authSystem', type=str, default=None, action='append')
        args = self.reqparse.parse_args()

        qry = db.User.order_by(User.username)
        if args['authSystem']:
            qry = qry.filter(User.auth_system.in_(args['authSystem']))

        total = qry.count()
        qry = qry.limit(args['count'])

        if (args['page'] - 1) > 0:
            offset = (args['page'] - 1) * args['count']
            qry = qry.offset(offset)

        users = qry.all()
        return self.make_response({
            'users': [x.to_json() for x in users],
            'userCount': total,
            'authSystems': list(current_app.available_auth_systems.keys()),
            'activeAuthSystem': current_app.active_auth_system.name
        })

    @rollback
    @check_auth(ROLE_ADMIN)
    def post(self):
        """Create a new user"""
        self.reqparse.add_argument('username', type=str, required=True)
        self.reqparse.add_argument('authSystem', type=str, required=True)
        self.reqparse.add_argument('password', type=str, required=False, default=None)
        self.reqparse.add_argument('roles', type=str, action='append', default=[])
        args = self.reqparse.parse_args()
        auditlog(event='user.create', actor=session['user'].username, data=args)

        user = db.User.find_one(
            User.username == args['username'],
            User.auth_system == args['authSystem']
        )
        roles = []
        if user:
            return self.make_response('User already exists', HTTP.BAD_REQUEST)

        if args['authSystem'] not in current_app.available_auth_systems:
            return self.make_response(
                'The {} auth system does not allow local edits'.format(args['authSystem']),
                HTTP.BAD_REQUEST
            )

        if current_app.available_auth_systems[args['authSystem']].readonly:
            return self.make_response(
                'You cannot create users for the {} auth system as it is handled externally'.format(args['authSystem']),
                HTTP.BAD_REQUEST
            )

        for roleName in args['roles']:
            role = db.Role.find_one(Role.name == roleName)

            if not role:
                return self.make_response('No such role {}'.format(roleName), HTTP.BAD_REQUEST)

            if roleName == ROLE_ADMIN and ROLE_ADMIN not in session['user'].roles:
                self.log.error('User {} tried to grant admin privileges to {}'.format(
                    session['user'].username,
                    args['username']
                ))

                return self.make_response('You do not have permission to grant admin privileges', HTTP.FORBIDDEN)

            roles.append(role)

        authSys = current_app.available_auth_systems[args['authSystem']]
        password = args['password'] or generate_password()

        user = User()
        user.username = args['username']
        user.password = hash_password(password)
        user.auth_system = authSys.name
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        User.add_role(user, roles)

        return self.make_response({
            'message': 'User {}/{} has been created'.format(user.auth_system, user.username),
            'user': user,
            'password': password if not args['password'] else None
        })

    @rollback
    @check_auth(ROLE_ADMIN)
    def options(self):
        """Returns metadata information required for User Creation"""
        roles = db.Role.all()

        return self.make_response({
            'roles': roles,
            'authSystems': list(current_app.available_auth_systems.keys()),
            'activeAuthSystem': current_app.active_auth_system.name
        })


class UserDetails(BaseView):
    URLS = ['/api/v1/user/<int:user_id>']

    @rollback
    @check_auth(ROLE_ADMIN)
    def get(self, user_id):
        """Returns a specific user"""
        user = db.User.find_one(User.user_id == user_id)
        roles = db.Role.all()

        if not user:
            return self.make_response('Unable to find the user requested, might have been removed', HTTP.NOT_FOUND)

        return self.make_response({
            'user': user.to_json(),
            'roles': roles
        }, HTTP.OK)

    @rollback
    @check_auth(ROLE_ADMIN)
    def put(self, user_id):
        """Update a user object"""
        self.reqparse.add_argument('roles', type=str, action='append')
        args = self.reqparse.parse_args()
        auditlog(event='user.create', actor=session['user'].username, data=args)

        user = db.User.find_one(User.user_id == user_id)
        roles = db.Role.find(Role.name.in_(args['roles']))
        if not user:
            return self.make_response('No such user found: {}'.format(user_id), HTTP.NOT_FOUND)

        if user.username == 'admin' and user.auth_system == 'builtin':
            return self.make_response('You cannot modify the built-in admin user', HTTP.FORBIDDEN)

        user.roles = []
        for role in roles:
            if role in args['roles']:
                user.roles.append(role)

        db.session.add(user)
        db.session.commit()

        return self.make_response({'message': 'User roles updated'}, HTTP.OK)

    @rollback
    @check_auth(ROLE_ADMIN)
    def delete(self, user_id):
        """Delete a user"""
        auditlog(event='user.delete', actor=session['user'].username, data={'userId': user_id})
        if session['user'].user_id == user_id:
            return self.make_response(
                'You cannot delete the user you are currently logged in as',
                HTTP.FORBIDDEN
            )

        user = db.User.find_one(User.user_id == user_id)
        if not user:
            return self.make_response('No such user id found: {}'.format(user_id), HTTP.UNAUTHORIZED)

        if user.username == 'admin' and user.auth_system == 'builtin':
            return self.make_response('You cannot delete the built-in admin user', HTTP.FORBIDDEN)

        username = user.username
        auth_system = user.auth_system
        db.session.delete(user)
        db.session.commit()

        return self.make_response('User {}/{} has been deleted'.format(auth_system, username), HTTP.OK)


class PasswordReset(BaseView):
    URLS = ['/api/v1/user/password/<int:user_id>']

    @rollback
    @check_auth(ROLE_USER)
    def put(self, user_id):
        self.reqparse.add_argument('password', type=str, required=False)
        args = self.reqparse.parse_args()
        auditlog(event='user.passwordReset', actor=session['user'].username, data=args)

        user = db.User.find_one(User.user_id == user_id)
        if not user:
            return self.make_response('User not found', HTTP.NOT_FOUND)

        if ROLE_ADMIN not in session['user'].roles and user_id != session['user'].user_id:
            self.log.warning('{} tried to change the password for another user'.format(session['user'].user_id))
            return self.make_response('You cannot change other users passwords', HTTP.FORBIDDEN)

        authsys = current_app.available_auth_systems[user.auth_system]
        if authsys.readonly:
            return self.make_response(
                'You cannot reset passwords for the {} based users'.format(authsys.name),
                HTTP.FORBIDDEN
            )

        new_pass = args['password'] or generate_password()

        user.password = hash_password(new_pass)
        db.session.add(user)
        db.session.commit()

        return self.make_response({
            'user': user.to_json(),
            'newPassword': new_pass if not args['password'] else None
        }, HTTP.OK)
