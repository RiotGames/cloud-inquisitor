from click import confirm, prompt
from flask_script import Option

from cloud_inquisitor.app import initialize
from cloud_inquisitor.database import db
from cloud_inquisitor.plugins.commands import BaseCommand
from cloud_inquisitor.schema import Account


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

    def run(self, **kwargs):
        initialize()

        # If there are no accounts created, ask the user if he/she wants to create one now
        if not kwargs['headless_mode'] and not db.Account.find_one():
            if confirm('You have no accounts defined, do you wish to add the first account now?'):
                self.init_account()
