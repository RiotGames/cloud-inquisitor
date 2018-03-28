from flask import session

from cloud_inquisitor.app import _import_templates
from cloud_inquisitor.constants import ROLE_ADMIN, HTTP
from cloud_inquisitor.database import db
from cloud_inquisitor.log import auditlog
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.schema import Role, Template
from cloud_inquisitor.utils import MenuItem, diff
from cloud_inquisitor.wrappers import check_auth, rollback


class TemplateList(BaseView):
    URLS = ['/api/v1/templates']
    MENU_ITEMS = [
        MenuItem(
            'admin',
            'Templates',
            'template.list',
            'template',
            order=4
        )
    ]

    @rollback
    @check_auth(ROLE_ADMIN)
    def get(self):
        templates = db.Template.all()

        return self.make_response({
            'templates': templates,
            'templateCount': len(templates)
        })

    @rollback
    @check_auth(ROLE_ADMIN)
    def post(self):
        """Create a new template"""
        self.reqparse.add_argument('templateName', type=str, required=True)
        self.reqparse.add_argument('template', type=str, required=True)
        args = self.reqparse.parse_args()

        template = db.Template.find_one(template_name=args['templateName'])
        if template:
            return self.make_response('Template already exists, update the existing template instead', HTTP.CONFLICT)

        template = Template()
        template.template_name = args['templateName']
        template.template = args['template']

        db.session.add(template)
        db.session.commit()
        auditlog(event='template.create', actor=session['user'].username, data=args)

        return self.make_response('Template {} has been created'.format(template.template_name), HTTP.CREATED)

    @rollback
    @check_auth(ROLE_ADMIN)
    def put(self):
        """Re-import all templates, overwriting any local changes made"""
        try:
            _import_templates(force=True)
            return self.make_response('Imported templates')
        except:
            self.log.exception('Failed importing templates')
            return self.make_response('Failed importing templates', HTTP.SERVER_ERROR)


class TemplateGet(BaseView):
    URLS = ['/api/v1/template/<string:template_name>']

    @rollback
    @check_auth(ROLE_ADMIN)
    def get(self, template_name):
        """Get a specific template"""
        template = db.Template.find_one(template_name=template_name)

        if not template:
            return self.make_response('No such template found', HTTP.NOT_FOUND)

        return self.make_response({'template': template})

    @rollback
    @check_auth(ROLE_ADMIN)
    def put(self, template_name):
        """Update a template"""
        self.reqparse.add_argument('template', type=str, required=True)
        args = self.reqparse.parse_args()

        template = db.Template.find_one(template_name=template_name)

        if not template:
            return self.make_response('No such template found', HTTP.NOT_FOUND)

        changes = diff(template.template, args['template'])
        template.template = args['template']
        template.is_modified = True

        db.session.add(template)
        db.session.commit()
        auditlog(
            event='template.update',
            actor=session['user'].username,
            data={
                'template_name': template_name,
                'template_changes': changes
            }
        )

        return self.make_response('Template {} has been updated'.format(template_name))

    @rollback
    @check_auth(ROLE_ADMIN)
    def delete(self, template_name):
        """Delete a template"""
        template = db.Template.find_one(template_name=template_name)
        if not template:
            return self.make_response('No such template found', HTTP.NOT_FOUND)

        db.session.delete(template)
        db.session.commit()
        auditlog(event='template.delete', actor=session['user'].username, data={'template_name': template_name})

        return self.make_response({
            'message': 'Template has been deleted',
            'templateName': template_name
        })
