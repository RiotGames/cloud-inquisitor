import logging
import time
from abc import abstractmethod, ABC
from functools import partial

import jwt
from botocore.exceptions import ClientError, EndpointConnectionError
from flask import request, session, current_app

from cloud_inquisitor.database import get_db_connection
from cloud_inquisitor.constants import HTTP, ROLE_ADMIN
from cloud_inquisitor.plugins.views import BaseView
from cloud_inquisitor.utils import has_access, get_jwt_key_data


class __wrapper(ABC):
    """Base wrapper class, setting up a logger, as well as default `__get__` method

    Attributes:
        log (logging.Logger): An instance of logging.Logger
        func (`function`): A reference to the wrapped function
    """

    def __init__(self, *args):
        self.log = logging.getLogger('.'.join((
            self.__class__.__module__,
            self.__class__.__name__
        )))

        if not args:
            self.func = None
        else:
            if callable(args[0]):
                self.func = args[0]

    def __get__(self, instance, owner):
        return partial(self.__call__, instance)

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class retry(__wrapper):
    """Decorator class to handle retrying calls if an exception occurs, with an exponential backoff. If the function
    fails to execute without raising an exception 3 times, the exception is re-raised
    """

    def __call__(self, *args, **kwargs):
        tries, delay, backoff = 3, 2, 2

        while tries > 0:
            try:
                return self.func(*args, **kwargs)
            except ClientError as ex:
                rex = ex.response['Error']['Code']

                if rex == 'OptInRequired':
                    self.log.info('Service not enabled for {} / {}'.format(
                        args[0].account.account_name,
                        self.func.__name__
                    ))
                    break
                else:
                    tries -= 1
                    if tries <= 0:
                        raise

                    time.sleep(delay)
                    delay *= backoff
            except EndpointConnectionError as ex:
                self.log.error(ex)
                break


class rollback(__wrapper):
    """Decorator class to handle rolling back database transactions after a function is done running. If the wrapped
    function is a member of a BaseView class it will also return any exceptions as a proper API resopnse, else re-raise
    the exception thrown.

    Due to a caching mechanic within SQLAlchemy, we perform a rollback on every request regardless or we might end
    up getting stale data from a cached connection / existing transaction instead of live data.
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.db = get_db_connection()

    def __call__(self, *args, **kwargs):
        try:
            return self.func(*args, **kwargs)

        except Exception as ex:
            self.log.exception(ex)
            if issubclass(args[0].__class__, BaseView):
                return BaseView.make_response(str(ex), HTTP.BAD_REQUEST)
            else:
                raise

        finally:
            self.db.session.rollback()


class check_auth(__wrapper):
    """Decorator class to handle authentication checks for API endpoints. If the user is not authenticated it will
    return a 401 UNAUTHORIZED response to the user
    """

    def __init__(self, *args):
        super().__init__(*args)
        self.role = ROLE_ADMIN

        if isinstance(args[0], str):
            self.role = args[0]

        elif len(args) > 1:
            self.role = args[1]

        else:
            raise ValueError('Invalid argument passed to check_auth: {} ({})'.format(args[0], type(args[0])))

    def __get__(self, instance, owner):
        return partial(self.__call__, instance)

    def __check_auth(self, view):
        headers = {x[0]: x[1] for x in request.headers}
        if 'Authorization' in headers:
            try:
                token = jwt.decode(
                    headers['Authorization'],
                    get_jwt_key_data()
                )

                if token['auth_system'] != current_app.active_auth_system.name:
                    self.log.error('Token is from another auth_system ({}) than the current one ({})'.format(
                        token['auth_system'],
                        current_app.active_auth_system.name
                    ))

                    return view.make_unauth_response()

                if has_access(session['user'], self.role):
                    return

                self.log.error('User {} attempted to access page {} without permissions'.format(
                    session['user'].username,
                    request.path
                ))
                return view.make_unauth_response()

            except (jwt.DecodeError, jwt.ExpiredSignatureError) as ex:
                session.clear()
                view.log.info('Failed to decode signature or it had expired: {0}'.format(ex))
                return view.make_unauth_response()

        session.clear()
        view.log.info('Failed to detect Authorization header')
        return view.make_unauth_response()

    def __call__(self, *args, **kwargs):
        # If called with without decorator arguments
        if args and isinstance(args[0], BaseView):
            auth = self.__check_auth(args[0])
            if auth: return auth

            return self.func(*args, **kwargs)

        # If called with decorator arguments
        else:
            def wrapped(*wargs, **wkwargs):
                func = args[0]
                wauth = self.__check_auth(wargs[0])
                if wauth:
                    return wauth

                return func(*wargs, **wkwargs)

            return wrapped
