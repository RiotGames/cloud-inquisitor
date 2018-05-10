import json
import re
from base64 import b64encode

from flask import session, Response, current_app
from sqlalchemy import desc

from cloud_inquisitor.constants import ROLE_ADMIN, HTTP, ROLE_USER, AccountTypes
from cloud_inquisitor.database import db
from cloud_inquisitor.json_utils import InquisitorJSONEncoder, InquisitorJSONDecoder
from cloud_inquisitor.log import auditlog
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.schema import Account
from cloud_inquisitor.utils import MenuItem
from cloud_inquisitor.wrappers import rollback, check_auth


def validate_contacts(contacts):
    for contact in contacts:
        if contact['type'] in current_app.notifiers:
            if not re.match(current_app.notifiers[contact['type']], contact['value'], re.I):
                raise Exception('Invalid formatted contact for {}: {}'.format(contact['type'], contact['value']))
        else:
            raise Exception('Unsupported notification type: {}'.format(contact['type']))


def add_account(
        account_name, account_number, account_contacts,
        is_enabled=True, ad_groupbase=None, required_groups=None,
        update_account_id=None, auto_commit=True
):
    """
    Add or update an account.
    if update_account_id is None, we add a new account; Otherwise we update the account with update_account_id
    """
    if update_account_id:
        acct = db.Account.find_one(Account.account_id == update_account_id)
    else:
        acct = Account(
            account_name,
            account_number,
            account_contacts,
            is_enabled,
            ad_groupbase
        )
    acct.required_groups = required_groups if required_groups else {}

    db.session.add(acct)
    if auto_commit:
        db.session.commit()

    return acct


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
        qry = db.Account.order_by(desc(Account.enabled), Account.account_name)

        if ROLE_ADMIN not in session['user'].roles:
            qry = qry.filter(Account.account_id.in_(session['accounts']))  # NOQA

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
        self.reqparse.add_argument('contacts', type=dict, required=True, action='append')
        self.reqparse.add_argument('enabled', type=int, required=True, choices=(0, 1))
        self.reqparse.add_argument('requiredGroups', type=str, action='append', default=())
        self.reqparse.add_argument('adGroupBase', type=str, default=None)
        args = self.reqparse.parse_args()

        validate_contacts(args['contacts'])

        for key in ('accountName', 'accountNumber', 'contacts', 'enabled'):
            value = args[key]
            if type(value) == str:
                value = value.strip()

            if type(value) in (int, tuple, list, str):
                if not value:
                    raise Exception('{} cannot be empty'.format(key.replace('_', ' ').title()))
            else:
                raise ValueError('Invalid type: {} for value {} for argument {}'.format(type(value), value, key))

        if db.Account.filter_by(account_name=args['accountName']).count() > 0:
            raise Exception('Account already exists')

        acct = add_account(
            account_name=args['accountName'],
            account_number=args['accountNumber'].zfill(12),
            account_contacts=args['contacts'],
            is_enabled=args['enabled'],
            ad_groupbase=args['adGroupBase'],
            required_groups=json.dumps(args['requiredGroups'])
        )

        # Add the newly created account to the session so we can see it right away
        session['accounts'].append(acct.account_id)
        auditlog(event='account.create', actor=session['user'].username, data=args)

        return self.make_response({'message': 'Account created', 'accountId': acct.account_id}, HTTP.CREATED)


class AccountDetail(BaseView):
    URLS = ['/api/v1/account/<int:accountId>']

    @rollback
    @check_auth(ROLE_ADMIN)
    def get(self, accountId):
        """Fetch a single account"""
        account = db.Account.find_one(Account.account_id == accountId)
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
        self.reqparse.add_argument('contacts', type=dict, required=True, action='append')
        self.reqparse.add_argument('enabled', type=int, required=True, choices=(0, 1))
        self.reqparse.add_argument('requiredRoles', type=str, action='append', default=())
        self.reqparse.add_argument('adGroupBase', type=str, default=None)
        args = self.reqparse.parse_args()
        validate_contacts(args['contacts'])

        if not args['accountName'].strip():
            raise Exception('You must provide an account name')

        if not args['contacts']:
            raise Exception('You must provide at least one contact')

        acct = add_account(
            account_name=args['accountName'],
            account_number=args['accountNumber'].zfill(12),
            account_contacts=args['contacts'],
            is_enabled=args['enabled'],
            ad_groupbase=args['adGroupBase'],
            required_groups=json.dumps(args['requiredGroups']),
            update_account_id=accountId
        )
        auditlog(event='account.update', actor=session['user'].username, data=args)

        return self.make_response({'message': 'Object updated', 'account': acct.to_json(is_admin=True)})

    @rollback
    @check_auth(ROLE_ADMIN)
    def delete(self, accountId):
        """Delete an account"""
        acct = db.Account.find_one(Account.account_id == accountId)
        if not acct:
            raise Exception('No such account found')

        acct.delete()
        auditlog(event='account.delete', actor=session['user'].username, data={'accountId': accountId})

        return self.make_response('Account deleted')


class AccountImportExport(BaseView):
    URLS = ['/api/v1/account/imex']

    @rollback
    @check_auth(ROLE_ADMIN)
    def get(self):
        out = [ns.to_json(is_admin=True) for ns in db.Account.find()]

        auditlog(event='account.export', actor=session['user'].username, data={})
        return Response(
            response=b64encode(
                bytes(
                    json.dumps(out, cls=InquisitorJSONEncoder),
                    'utf-8'
                )
            ),
            status=HTTP.OK
        )

    @rollback
    @check_auth(ROLE_ADMIN)
    def post(self):
        self.reqparse.add_argument('config', type=str, required=True)
        args = self.reqparse.parse_args()

        try:
            account_data = json.loads(args['config'], cls=InquisitorJSONDecoder)

            for acctData in account_data:
                acct = Account.get(acctData['accountName'])

                if not getattr(AccountTypes, acctData['accountType'], None):
                    return self.make_response(
                        'Unsupported account type: {}'.format(acctData['accountType']),
                        HTTP.BAD_REQUEST
                    )

                add_account(
                    account_name=args['accountName'],
                    account_number=args['accountNumber'].zfill(12),
                    account_contacts=args['contacts'],
                    is_enabled=args['enabled'],
                    ad_groupbase=args['adGroupBase'],
                    required_groups=json.dumps(args['requiredGroups']),
                    update_account_id=None if not acct else acct.account_id,
                    auto_commit=False
                )

            db.session.commit()
            auditlog(event='account.import', actor=session['user'].username, data={})

            return self.make_response({'message': 'Accounts imported'})
        except Exception as ex:
            self.log.exception('Failed importing configuration data')
            return self.make_response(
                'Error importing account data: {}'.format(ex),
                HTTP.SERVER_ERROR
            )
