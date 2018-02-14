from flask import session

from cloud_inquisitor.constants import ROLE_ADMIN, HTTP
from cloud_inquisitor.database import db
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.schema import Role, AuditLog
from cloud_inquisitor.utils import MenuItem
from cloud_inquisitor.wrappers import check_auth, rollback


class RoleList(BaseView):
    URLS = ['/api/v1/roles']
    MENU_ITEMS = [
        MenuItem(
            'admin',
            'Roles',
            'role.list',
            'role',
            order=4,
            args={
                'page': 1,
                'count': 25
            }
        )
    ]

    @rollback
    @check_auth(ROLE_ADMIN)
    def get(self):
        roles = db.Role.all()

        return self.make_response({
            'roles': roles,
            'roleCount': len(roles)
        })

    @rollback
    @check_auth(ROLE_ADMIN)
    def post(self):
        """Create a new role"""
        self.reqparse.add_argument('name', type=str, required=True)
        self.reqparse.add_argument('color', type=str, required=True)
        args = self.reqparse.parse_args()
        AuditLog.log('role.create', session['user'].username, args)

        role = Role()
        role.name = args['name']
        role.color = args['color']

        db.session.add(role)
        db.session.commit()

        return self.make_response('Role {} has been created'.format(role.role_id), HTTP.CREATED)


class RoleGet(BaseView):
    URLS = ['/api/v1/role/<int:roleId>']

    @rollback
    @check_auth(ROLE_ADMIN)
    def get(self, roleId):
        """Get a specific role information"""
        role = db.Role.find_one(Role.role_id == roleId)

        if not role:
            return self.make_response('No such role found', HTTP.NOT_FOUND)

        return self.make_response({'role': role})

    @rollback
    @check_auth(ROLE_ADMIN)
    def put(self, roleId):
        """Update a user role"""
        self.reqparse.add_argument('color', type=str, required=True)
        args = self.reqparse.parse_args()
        AuditLog.log('role.update', session['user'].username, args)

        role = db.Role.find_one(Role.role_id == roleId)
        if not role:
            self.make_response({
                'message': 'No such role found'
            }, HTTP.NOT_FOUND)

        role.color = args['color']

        db.session.add(role)
        db.session.commit()

        return self.make_response('Role {} has been updated'.format(role.name))

    @rollback
    @check_auth(ROLE_ADMIN)
    def delete(self, roleId):
        """Delete a user role"""
        AuditLog.log('role.delete', session['user'].username, {'roleId': roleId})

        role = db.Role.find_one(Role.role_id == roleId)
        if not role:
            return self.make_response('No such role found', HTTP.NOT_FOUND)

        if role.name in ('User', 'Admin'):
            return self.make_response('Cannot delete the built-in roles', HTTP.BAD_REQUEST)

        db.session.delete(role)
        db.session.commit()

        return self.make_response('Role has been deleted')
