from abc import abstractproperty

from click import confirm, prompt
from cloud_inquisitor.app import initialize
from flask_script import Option
from pkg_resources import iter_entry_points

from cloud_inquisitor.constants import PLUGIN_NAMESPACES, DEFAULT_CONFIG_OPTIONS
from cloud_inquisitor.database import db
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
        nsobj = db.ConfigNamespace.find_one(ConfigNamespace.namespace_prefix == prefix)
        if not nsobj:
            self.log.info('Adding namespace {}'.format(name))
            nsobj = ConfigNamespace()
            nsobj.namespace_prefix = prefix
            nsobj.name = name
            nsobj.sort_order = sort_order
        return nsobj

    def register_default_option(self, nsobj, opt):
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
        initialize()

        # If there are no accounts created, ask the user if he/she wants to create one now
        if not kwargs['headless_mode'] and not db.Account.find_one():
            if confirm('You have no accounts defined, do you wish to add the first account now?'):
                self.init_account()
