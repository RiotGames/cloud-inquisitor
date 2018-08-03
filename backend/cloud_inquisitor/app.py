"""Contains the Flask app for the REST API"""
import logging
import os
import sys
from abc import abstractproperty
from pkg_resources import resource_filename

from flask import Flask, request, session, abort
from flask_compress import Compress
from flask_restful import Api
from flask_script import Server
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError

from cloud_inquisitor import app_config, CINQ_PLUGINS
from cloud_inquisitor.config import dbconfig, DBCChoice
from cloud_inquisitor.constants import DEFAULT_MENU_ITEMS, DEFAULT_CONFIG_OPTIONS
from cloud_inquisitor.database import db
from cloud_inquisitor.json_utils import InquisitorJSONDecoder, InquisitorJSONEncoder
from cloud_inquisitor.log import auditlog
from cloud_inquisitor.plugins.views import BaseView, LoginRedirectView, LogoutRedirectView
from cloud_inquisitor.schema import ResourceType, ConfigNamespace, ConfigItem, Role, Template
from cloud_inquisitor.utils import get_hash, diff

logger = logging.getLogger(__name__.split('.')[0])

__initialized = False


# region Helper functions
def _get_config_namespace(prefix, name, sort_order=2):
    nsobj = db.ConfigNamespace.find_one(ConfigNamespace.namespace_prefix == prefix)
    if not nsobj:
        logger.info('Adding namespace {}'.format(name))
        nsobj = ConfigNamespace()
        nsobj.namespace_prefix = prefix
        nsobj.name = name
        nsobj.sort_order = sort_order
    return nsobj

def _register_default_option(nsobj, opt):
    """ Register default ConfigOption value if it doesn't exist. If does exist, update the description if needed """
    item = ConfigItem.get(nsobj.namespace_prefix, opt.name)
    if not item:
        logger.info('Adding {} ({}) = {} to {}'.format(
            opt.name,
            opt.type,
            opt.default_value,
            nsobj.namespace_prefix
        ))
        item = ConfigItem()
        item.namespace_prefix = nsobj.namespace_prefix
        item.key = opt.name
        item.value = opt.default_value
        item.type = opt.type
        item.description = opt.description
        nsobj.config_items.append(item)
    else:
        if item.description != opt.description:
            logger.info('Updating description of {} / {}'.format(item.namespace_prefix, item.key))
            item.description = opt.description
            db.session.add(item)

def _add_default_roles():
    roles = {
        'Admin': '#BD0000',
        'NOC': '#5B5BFF',
        'User': '#008000'
    }

    for name, color in roles.items():
        if not Role.get(name):
            role = Role()
            role.name = name
            role.color = color
            db.session.add(role)
            logger.info('Added standard role {} ({})'.format(name, color))

def _import_templates(force=False):
    """Import templates from disk into database

    Reads all templates from disk and adds them to the database. By default, any template that has been modified by
    the user will not be updated. This can however be changed by setting `force` to `True`, which causes all templates
    to be imported regardless of status

    Args:
        force (`bool`): Force overwrite any templates with local changes made. Default: `False`

    Returns:
        `None`
    """
    tmplpath = os.path.join(resource_filename('cloud_inquisitor', 'data'), 'templates')
    disk_templates = {f: os.path.join(root, f) for root, directory, files in os.walk(tmplpath) for f in files}
    db_templates = {tmpl.template_name: tmpl for tmpl in db.Template.find()}

    for name, template_file in disk_templates.items():
        with open(template_file, 'r') as f:
            body = f.read()
        disk_hash = get_hash(body)

        if name not in db_templates:
            template = Template()
            template.template_name = name
            template.template = body

            db.session.add(template)
            auditlog(
                event='template.import',
                actor='init',
                data={
                    'template_name': name,
                    'template': body
                }
            )
            logger.info('Imported template {}'.format(name))
        else:
            template = db_templates[name]
            db_hash = get_hash(template.template)

            if db_hash != disk_hash:
                if force or not db_templates[name].is_modified:
                    template.template = body

                    db.session.add(template)
                    auditlog(
                        event='template.update',
                        actor='init',
                        data={
                            'template_name': name,
                            'template_diff': diff(template.template, body)
                        }
                    )
                    logger.info('Updated template {}'.format(name))
                else:
                    logger.warning(
                        'Updated template available for {}. Will not import as it would'
                        ' overwrite user edited content and force is not enabled'.format(name)
                    )
# endregion


def initialize():
    """Initialize the application configuration, adding any missing default configuration or roles

    Returns:
        `None`
    """
    global __initialized

    if __initialized:
        return

    # Setup all the default base settings
    try:
        for data in DEFAULT_CONFIG_OPTIONS:
            nsobj = _get_config_namespace(data['prefix'], data['name'], sort_order=data['sort_order'])
            for opt in data['options']:
                _register_default_option(nsobj, opt)
            db.session.add(nsobj)

        # Iterate over all of our plugins and setup their defaults
        for ns, info in CINQ_PLUGINS.items():
            if info['name'] == 'commands':
                continue

            for entry_point in info['plugins']:
                _cls = entry_point.load()
                if hasattr(_cls, 'ns'):
                    ns_name = '{}: {}'.format(info['name'].capitalize(), _cls.name)
                    if not isinstance(_cls.options, abstractproperty):
                        nsobj = _get_config_namespace(_cls.ns, ns_name)
                        if _cls.options:
                            for opt in _cls.options:
                                _register_default_option(nsobj, opt)

                        db.session.add(nsobj)

        # Create the default roles if they are missing and import any missing or updated templates,
        # if they havent been modified by the user
        _add_default_roles()
        _import_templates()

        db.session.commit()
        dbconfig.reload_data()
        __initialized = True
    except ProgrammingError as ex:
        if str(ex).find('1146') != -1:
            logging.getLogger('cloud_inquisitor').error(
                'Missing required tables, please make sure you run `cloud-inquisitor db upgrade`'
            )


class ServerWrapper(Server):
    """Wrapper class for the built-in runserver functionality, which registers views before calling Flask's
    ServerWrapper
    """
    def __call__(self, app, *args, **kwargs):
        app.register_plugins()
        super().__call__(app, *args, **kwargs)


class CINQFlask(Flask):
    """Wrapper class for the Flask application. Takes case of setting up all the settings require for flask to run
    """
    json_encoder = InquisitorJSONEncoder
    json_decoder = InquisitorJSONDecoder

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api = None
        self.active_auth_system = None
        self.types = {}
        self.available_auth_systems = {}
        self.menu_items = DEFAULT_MENU_ITEMS

        self.config['DEBUG'] = app_config.log_level == 'DEBUG'
        self.config['SECRET_KEY'] = app_config.flask.secret_key

        initialize()
        self.api = CINQApi(self)

        self.notifiers = self.__register_notifiers()

    def register_plugins(self):
        self.__register_types()
        self.api.register_views(self)

    def register_auth_system(self, auth_system):
        """Register a given authentication system with the framework. Returns `True` if the `auth_system` is registered
        as the active auth system, else `False`

        Args:
            auth_system (:obj:`BaseAuthPlugin`): A subclass of the `BaseAuthPlugin` class to register

        Returns:
            `bool`
        """
        auth_system_settings = dbconfig.get('auth_system')

        if auth_system.name not in auth_system_settings['available']:
            auth_system_settings['available'].append(auth_system.name)
            dbconfig.set('default', 'auth_system', DBCChoice(auth_system_settings))

        if auth_system.name == auth_system_settings['enabled'][0]:
            self.active_auth_system = auth_system
            auth_system().bootstrap()
            logger.debug('Registered {} as the active auth system'.format(auth_system.name))
            return True

        else:
            logger.debug('Not trying to load the {} auth system as it is disabled by config'.format(auth_system.name))
            return False

    def register_menu_item(self, items):
        """Registers a views menu items into the metadata for the application. Skip if the item is already present

        Args:
            items (`list` of `MenuItem`): A list of `MenuItem`s

        Returns:
            `None`
        """
        for itm in items:
            if itm.group in self.menu_items:
                # Only add the menu item if we don't already have it registered
                if itm not in self.menu_items[itm.group]['items']:
                    self.menu_items[itm.group]['items'].append(itm)
            else:
                logger.warning('Tried registering menu item to unknown group {}'.format(itm.group))

    # region Helper methods
    def __register_types(self):
        """Iterates all entry points for resource types and registers a `resource_type_id` to class mapping

        Returns:
            `None`
        """
        try:
            for entry_point in CINQ_PLUGINS['cloud_inquisitor.plugins.types']['plugins']:
                cls = entry_point.load()
                self.types[ResourceType.get(cls.resource_type).resource_type_id] = cls
                logger.debug('Registered resource type {}'.format(cls.__name__))
        except SQLAlchemyError as ex:
            logger.warning('Failed loading type information: {}'.format(ex))

    def __register_notifiers(self):
        """Lists all notifiers to be able to provide metadata for the frontend

        Returns:
            `list` of `dict`
        """
        notifiers = {}
        for entry_point in CINQ_PLUGINS['cloud_inquisitor.plugins.notifiers']['plugins']:
            cls = entry_point.load()
            notifiers[cls.notifier_type] = cls.validation

        return notifiers
    # endregion


class CINQApi(Api):
    """Wrapper around the flask_restful API class."""

    def register_views(self, app):
        """Iterates all entry points for views and auth systems and dynamically load and register the routes with Flask

        Args:
            app (`CINQFlask`): CINQFlask object to register views for

        Returns:
            `None`
        """
        self.add_resource(LoginRedirectView, '/auth/login')
        self.add_resource(LogoutRedirectView, '/auth/logout')

        for entry_point in CINQ_PLUGINS['cloud_inquisitor.plugins.auth']['plugins']:
            cls = entry_point.load()
            app.available_auth_systems[cls.name] = cls

            if app.register_auth_system(cls):
                for vcls in cls.views:
                    self.add_resource(vcls, *vcls.URLS)
                    logger.debug('Registered auth system view {} for paths: {}'.format(
                        cls.__name__,
                        ', '.join(vcls.URLS)
                    ))

        if not app.active_auth_system:
            logger.error('No auth systems active, please enable an auth system and then start the system again')
            sys.exit(-1)

        for entry_point in CINQ_PLUGINS['cloud_inquisitor.plugins.views']['plugins']:
            view = entry_point.load()
            self.add_resource(view, *view.URLS)
            app.register_menu_item(view.MENU_ITEMS)

            logger.debug('Registered view {} for paths: {}'.format(view.__name__, ', '.join(view.URLS)))


def before_request():
    """Checks to ensure that the session is valid and validates the users CSRF token is present

    Returns:
        `None`
    """
    if not request.path.startswith('/saml') and not request.path.startswith('/auth'):
        # Validate the session has the items we need
        if 'accounts' not in session:
            logger.debug('Missing \'accounts\' from session object, sending user to login page')
            return BaseView.make_unauth_response()

        # Require the CSRF token to be present if we are performing a change action (add, delete or modify objects)
        # but exclude the SAML endpoints from the CSRF check
        if request.method in ('POST', 'PUT', 'DELETE',):
            if session['csrf_token'] != request.headers.get('X-Csrf-Token'):
                logger.info('CSRF Token is missing or incorrect, sending user to login page')
                abort(403)


def after_request(response):
    """Modifies the response object prior to sending it to the client. Used to add CORS headers to the request

    Args:
        response (response): Flask response object

    Returns:
        `None`
    """
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


def create_app():
    app = CINQFlask(__name__)

    # Setup before/after request handlers
    app.before_request(before_request)
    app.after_request(after_request)

    Compress(app)

    return app
