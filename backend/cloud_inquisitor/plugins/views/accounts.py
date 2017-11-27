import json

from flask import session
from sqlalchemy import desc

from cloud_inquisitor import db
from cloud_inquisitor.constants import ROLE_ADMIN, HTTP, ROLE_USER
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.schema import Account, AuditLog
from cloud_inquisitor.utils import validate_email, MenuItem
from cloud_inquisitor.wrappers import rollback, check_auth


class AccountList(BaseView):
    URLS = ['/api/v1/account']
    MENU_ITEMS = [
        MenuItem(
            'admin',
            'Accounts',
            'account.list',
            'account',
            order=1
        )
    ]

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        """List all accounts"""
        qry = Account.query.order_by(desc(Account.enabled), Account.account_name)

        if ROLE_ADMIN not in session['user'].roles:
            qry = qry.filter(Account.account_id.in_(session['accounts']))

        accounts = qry.all()

        if accounts:
            return self.make_response({
                'message': None,
                'accounts': [x.to_json(is_admin=ROLE_ADMIN in session['user'].roles or False) for x in accounts]
            })
        else:
            return self.make_response({
                'message': 'Unable to find any accounts',
                'accounts': None
            }, HTTP.NOT_FOUND)

    @rollback
    @check_auth(ROLE_ADMIN)
    def post(self):
        """Create a new account"""
        self.reqparse.add_argument('accountName', type=str, required=True)
        self.reqparse.add_argument('accountNumber', type=str, required=True)
        self.reqparse.add_argument('contacts', type=str, required=True, action='append')
        self.reqparse.add_argument('enabled', type=int, required=True, choices=(0, 1))
        self.reqparse.add_argument('requiredGroups', type=str, action='append', default=())
        self.reqparse.add_argument('adGroupBase', type=str, default=None)
        args = self.reqparse.parse_args()
        AuditLog.log('account.create', session['user'].username, args)

        for contact in args['contacts']:
            if not contact.startswith('#') and (contact.find('@') >= 0 and not validate_email(contact)):
                raise Exception('Invalid email address or slack channel name supplied: {}'.format(contact))

        for key in ('accountName', 'accountNumber', 'contacts', 'enabled'):
            value = args[key]
            if type(value) == str:
                value = value.strip()

            if type(value) in (int, tuple, list, str):
                if not value:
                    raise Exception('{} cannot be empty'.format(key.replace('_', ' ').title()))
            else:
                raise ValueError('Invalid type: {} for value {} for argument {}'.format(type(value), value, key))

        if Account.query.filter_by(account_name=args['accountName']).count() > 0:
            raise Exception('Account already exists')

        acct = Account(
            args['accountName'],
            args['accountNumber'].zfill(12),
            args['contacts'],
            args['enabled'],
            args['adGroupBase']
        )
        acct.required_groups = json.dumps(args['requiredGroups'])
        db.session.add(acct)
        db.session.commit()

        # Add the newly created account to the session so we can see it right away
        session['accounts'].append(acct.account_id)
        return self.make_response({'message': 'Account created', 'accountId': acct.account_id}, HTTP.CREATED)


class AccountDetail(BaseView):
    URLS = ['/api/v1/account/<int:accountId>']

    @rollback
    @check_auth(ROLE_ADMIN)
    def get(self, accountId):
        """Fetch a single account"""
        account = Account.query.filter_by(account_id=accountId).first()
        if account:
            return self.make_response({
                'message': None,
                'account': account.to_json(is_admin=True)
            })
        else:
            return self.make_response({
                'message': 'Unable to find account',
                'account': None
            }, HTTP.NOT_FOUND)

    @rollback
    @check_auth(ROLE_ADMIN)
    def put(self, accountId):
        """Update an account"""
        self.reqparse.add_argument('accountName', type=str, required=True)
        self.reqparse.add_argument('accountNumber', type=str, required=True)
        self.reqparse.add_argument('contacts', type=str, required=True, action='append')
        self.reqparse.add_argument('enabled', type=int, required=True, choices=(0, 1))
        self.reqparse.add_argument('requiredRoles', type=str, action='append', default=())
        self.reqparse.add_argument('adGroupBase', type=str, default=None)
        args = self.reqparse.parse_args()
        AuditLog.log('account.update', session['user'].username, args)

        for contact in args['contacts']:
            if not contact.startswith('#') and not validate_email(contact):
                raise Exception('Invalid email address or slack channel name supplied: {}'.format(contact))

        if not args['accountName'].strip():
            raise Exception('You must provide an account name')

        if not args['contacts']:
            raise Exception('You must provide at least one contact')

        acct = Account.query.filter_by(account_id=accountId).first()
        acct.account_name = args['accountName']
        acct.account_number = args['accountNumber'].zfill(12)
        acct.contacts = args['contacts']
        acct.enabled = args['enabled']
        acct.required_roles = args['requiredRoles']
        acct.ad_group_base = args['adGroupBase']

        db.session.add(acct)
        db.session.commit()

        return self.make_response({'message': 'Object updated', 'account': acct.to_json(is_admin=True)})

    @rollback
    @check_auth(ROLE_ADMIN)
    def delete(self, accountId):
        """Delete an account"""
        AuditLog.log('account.delete', session['user'].username, {'accountId': accountId})
        acct = Account.query.filter_by(account_id=accountId).first()
        if not acct:
            raise Exception('No such account found')

        acct.delete()

        return self.make_response('Account deleted')
