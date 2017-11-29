from abc import abstractproperty

from click import confirm, prompt
from flask_script import Option
from pkg_resources import iter_entry_points

from cloud_inquisitor import db
from cloud_inquisitor.config import ConfigOption
from cloud_inquisitor.constants import PLUGIN_NAMESPACES
from cloud_inquisitor.plugins.commands import BaseCommand
from cloud_inquisitor.schema import ConfigNamespace, ConfigItem, Account, Role


class Setup(BaseCommand):
    """Sets up the initial state of the configuration stored in the database"""
    name = 'Setup'
    option_list = (
        Option(
            '-H', '--headless',
            dest='headless_mode',
            action='store_true',
            help='Setup command will not prompt for interactive input'
        ),
    )

    def init_account(self):
        """Create a new account object"""
        account_name = prompt('Account name', type=str)
        account_number = prompt('Account ID Number', type=int)
        contacts = prompt('Contacts', type=str)
        if confirm('Limit access to this account?'):
            required_roles = prompt('Required Role (optional)', type=str)
        else:
            required_roles = ''
        enabled = confirm('Enabled')

        acct = Account()
        acct.account_name = account_name
        acct.account_number = account_number
        acct.contacts = list(map(lambda x: x.strip(), contacts.split(',')))
        acct.enabled = enabled
        acct.required_roles = [x for x in map(lambda x: x.strip(), required_roles.split(',')) if x]

        db.session.add(acct)
        db.session.commit()

        self.log.info('Account has been added')

    def get_config_namespace(self, prefix, name, sort_order=2):
        nsobj = ConfigNamespace.query.filter(ConfigNamespace.namespace_prefix == prefix).first()
        if not nsobj:
            self.log.info('Adding namespace {}'.format(name))
            nsobj = ConfigNamespace()
            nsobj.namespace_prefix = prefix
            nsobj.name = name
            nsobj.sort_order = sort_order
        return nsobj

    def register_default_option(self, nsobj: ConfigNamespace, opt: ConfigOption):
        """ Register default ConfigOption value if it doesn't exist. If does exist, update the description if needed """
        item = ConfigItem.get(nsobj.namespace_prefix, opt.name)
        if not item:
            self.log.info('Adding {} ({}) = {} to {}'.format(
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
                self.log.info('Updating description of {} / {}'.format(item.namespace_prefix, item.key))
                item.description = opt.description
                db.session.add(item)

    def add_default_roles(self):
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
                self.log.info('Added standard role {} ({})'.format(name, color))

        db.session.commit()

    def run(self, **kwargs):
        # Setup the base application settings
        defaults = [
            {
                'prefix': 'default',
                'name': 'Default',
                'sort_order': 0,
                'options': [
                    ConfigOption('debug', False, 'bool', 'Enable debug mode for flask'),
                    ConfigOption('session_expire_time', 43200, 'int', 'Time in seconds before sessions expire'),
                    ConfigOption('role_name', 'cinq_role', 'string',
                                 'Role name Cloud Inquisitor will use in each account'),
                    ConfigOption('ignored_aws_regions_regexp', '(^cn-|GLOBAL|-gov)', 'string',
                                 'A regular expression used to filter out regions from the AWS static data'),
                    ConfigOption(
                        name='auth_system',
                        default_value={
                            'enabled': ['Local Authentication'],
                            'available': ['Local Authentication'],
                            'max_items': 1,
                            'min_items': 1
                        },
                        type='choice',
                        description='Enabled authentication module'
                    ),
                    ConfigOption('scheduler', 'StandaloneScheduler', 'string', 'Default scheduler module'),
                    ConfigOption('jwt_key_file_path', 'ssl/private.key', 'string',
                                 'Path to the private key used to encrypt JWT session tokens. Can be relative to the '
                                 'folder containing the configuration file, or absolute path')
                ],
            },
            {
                'prefix': 'log',
                'name': 'Logging',
                'sort_order': 1,
                'options': [
                    ConfigOption('log_level', 'INFO', 'string', 'Log level'),
                    ConfigOption('enable_syslog_forwarding', False, 'bool',
                                 'Enable forwarding logs to remote log collector'),
                    ConfigOption('remote_syslog_server_addr', '127.0.0.1', 'string',
                                 'Address of the remote log collector'),
                    ConfigOption('remote_syslog_server_port', 514, 'string', 'Port of the remote log collector'),
                    ConfigOption('log_keep_days', 31, 'int', 'Delete log entries older than n days'),
                ],
            },
            {
                'prefix': 'api',
                'name': 'API',
                'sort_order': 2,
                'options': [
                    ConfigOption('host', '127.0.0.1', 'string', 'Host of the API server'),
                    ConfigOption('port', 5000, 'int', 'Port of the API server'),
                    ConfigOption('workers', 6, 'int', 'Number of worker processes spawned for the API')
                ]
            },
        ]

        # Setup all the default base settings
        for data in defaults:
            nsobj = self.get_config_namespace(data['prefix'], data['name'], sort_order=data['sort_order'])
            for opt in data['options']:
                self.register_default_option(nsobj, opt)
            db.session.add(nsobj)
            db.session.commit()

        # Iterate over all of our plugins and setup their defaults
        for ptype, namespaces in list(PLUGIN_NAMESPACES.items()):
            for ns in namespaces:
                for ep in iter_entry_points(ns):
                    cls = ep.load()
                    if hasattr(cls, 'ns'):
                        ns_name = '{}: {}'.format(ptype.capitalize(), cls.name)
                        nsobj = self.get_config_namespace(cls.ns, ns_name)
                        if not isinstance(cls.options, abstractproperty):
                            if cls.options:
                                for opt in cls.options:
                                    self.register_default_option(nsobj, opt)
                        db.session.add(nsobj)
                        db.session.commit()

        # Create the default roles if they are missing
        self.add_default_roles()

        # If there are no accounts created, ask the user if he/she wants to create one now
        if not kwargs['headless_mode'] and not Account.query.first():
            if confirm('You have no accounts defined, do you wish to add the first account now?'):
                self.init_account()
