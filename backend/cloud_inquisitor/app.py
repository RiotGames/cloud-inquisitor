"""Contains the Flask app for the REST API"""
import logging
import sys

from flask import Flask, request, session, abort
from flask_compress import Compress
from flask_restful import Api
from pkg_resources import iter_entry_points
from sqlalchemy.exc import SQLAlchemyError

from cloud_inquisitor import app_config
from cloud_inquisitor.config import dbconfig, DBCChoice
from cloud_inquisitor.constants import DEFAULT_MENU_ITEMS
from cloud_inquisitor.json_utils import InquisitorJSONDecoder, InquisitorJSONEncoder
from cloud_inquisitor.plugins.views import BaseView, LoginRedirectView, LogoutRedirectView
from cloud_inquisitor.schema import ResourceType

logger = logging.getLogger(__name__.split('.')[0])


class CINQFlask(Flask):
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

        self.api = CINQApi(self)
        self.__register_types()

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

    def __register_types(self):
        """Iterates all entry points for resource types and registers a `resource_type_id` to class mapping

        Returns:
            `None`
        """
        try:
            for ep in iter_entry_points('cloud_inquisitor.plugins.types'):
                cls = ep.load()
                self.types[ResourceType.get(cls.resource_type).resource_type_id] = cls
                logger.debug('Registered resource type {}'.format(cls.__name__))
        except SQLAlchemyError as ex:
            logger.warning('Failed loading type information: {}'.format(ex))


class CINQApi(Api):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_views(self.app)

    def register_views(self, app):
        """Iterates all entry points for views and auth systems and dynamically load and register the routes with Flask

        Args:
            app (`CINQFlask`): CINQFlask object to register views for

        Returns:
            `None`
        """
        self.add_resource(LoginRedirectView, '/auth/login')
        self.add_resource(LogoutRedirectView, '/auth/logout')

        for ep in iter_entry_points('cloud_inquisitor.plugins.auth'):
            cls = ep.load()
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

        for ep in iter_entry_points('cloud_inquisitor.plugins.views'):
            view = ep.load()
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
