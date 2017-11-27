from flask_script import Option
from pkg_resources import iter_entry_points

from cloud_inquisitor import app
from cloud_inquisitor.constants import PLUGIN_NAMESPACES
from cloud_inquisitor.plugins.commands import BaseCommand


class Auth(BaseCommand):
    """Changes the active auth plugin and bootstraps the new system if needed"""
    name = 'Auth'
    option_list = (
        Option(
            '-a', '--auth-system',
            dest='authsys',
            type=str,
            help='Name of the auth system to set as the active'
        ),
        Option(
            '-l', '--list',
            dest='list',
            action='store_true',
            default=False
        )
    )

    def run(self, **kwargs):
        plugins = {}
        namespaces = PLUGIN_NAMESPACES['auth']
        for ns in namespaces:
            for ep in iter_entry_points(ns):
                cls = ep.load()
                plugins[cls.name] = cls
                app.register_auth_system(cls)

        if kwargs['list']:
            self.log.info('--- List of available auth systems ---')
            for name, authsys in list(plugins.items()):
                if app.active_auth_system == authsys:
                    self.log.info('{} (active)'.format(name))
                else:
                    self.log.info(name)
            self.log.info('--- End list of Auth Systems ---')

        elif kwargs['authsys']:
            if kwargs['authsys'] in plugins:
                if app.active_auth_system and kwargs['authsys'] == app.active_auth_system.name:
                    self.log.info('{} is already the active auth system'.format(kwargs['authsys']))
                else:
                    for name, authsys in list(plugins.items()):
                        state = (name == kwargs['authsys'])
                        self.dbconfig.set(authsys.ns, 'enabled', state)
                        self.log.info('{} {}'.format('Enabled' if state else 'Disabled', name))
            else:
                self.log.error('Invalid auth system: {}'.format(kwargs['authsys']))

        else:
            print('You must use either -a or -l')
