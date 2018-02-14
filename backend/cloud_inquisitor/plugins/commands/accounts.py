from click import confirm, prompt
from flask_script import Option

from cloud_inquisitor.database import db
from cloud_inquisitor.plugins.commands import BaseCommand
from cloud_inquisitor.schema import Account


class AddAccount(BaseCommand):
    """Adds a new AWS account to the system"""
    name = 'AddAccount'
    option_list = (
        Option('account_name', help='Account Name', metavar='NAME', nargs='?', type=str),
        Option('account_number', help='AWS Account number', metavar='ACCOUNT_NUMBER', nargs='?', type=int),
        Option('contacts', help='Contact emails and slack channels', metavar='contacts', nargs='?', type=str),
        Option('--disabled', '-d', help='Disable the account', action='store_true', default=False),
        Option('--update', help='If account already exists, update it', action='store_true', default=False)
    )

    def run(self, **kwargs):
        try:
            if not kwargs['account_name']:
                kwargs['account_name'] = prompt('Account name')

            if not kwargs['account_number']:
                kwargs['account_number'] = prompt('Account number')

            if not kwargs['contacts']:
                kwargs['contacts'] = prompt('Contacts')

            acct = db.Account.find_one(Account.account_name == kwargs['account_name'])
            if acct:
                if kwargs['update']:
                    acct.contacts = kwargs['contacts'].split(',')
                    acct.active = not kwargs['disabled']
                    acct.account_number = kwargs['account_number']

                    db.session.add(acct)
                    db.session.commit()
                    self.log.info('Updated {0}'.format(acct.account_name))
                else:
                    self.log.warn('Account {0} already exists'.format(kwargs['account_name']))
            else:
                acct = Account(
                    kwargs['account_name'],
                    kwargs['account_number'],
                    kwargs['contacts'].split(','),
                    not kwargs['disabled']
                )
                db.session.add(acct)
                db.session.commit()
                self.log.info('Account {0} has been added (account id: {1})'.format(acct.account_name, acct.account_id))

        except Exception:
            self.log.exception('An error occured while trying to add the account')
            db.session.rollback()


class DeleteAccount(BaseCommand):
    """Deletes an AWS account and all objects that are related to the account"""
    name = 'DeleteAccount'
    option_list = (
        Option('account_name', help='Account Name', metavar='NAME'),
    )

    def run(self, **kwargs):
        try:
            acct = db.Account.find_one(Account.account_name == kwargs['account_name'])
            if acct:
                cfm = 'Are you absolutely sure you wish to delete the account named {}'.format(acct.account_name)
                if confirm(cfm):
                    acct.delete()
                    self.log.info('Account {0} has been deleted'.format(kwargs['account_name']))
                else:
                    self.log.info('Failed to verify account name, not deleting')
            else:
                self.log.warning('No such account found: {0}'.format(kwargs['account_name']))

        except Exception:
            self.log.exception('An error occured while trying to delete the account')
            db.session.rollback()
