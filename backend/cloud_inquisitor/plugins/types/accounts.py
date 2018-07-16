import logging
from abc import ABC, abstractmethod
from datetime import datetime

from cloud_inquisitor.constants import PLUGIN_NAMESPACES
from sqlalchemy import and_, or_, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased

from cloud_inquisitor import get_plugin_by_name
from cloud_inquisitor.database import db
from cloud_inquisitor.exceptions import AccountException, InquisitorError
from cloud_inquisitor.schema import AccountProperty, Account, AccountType
from cloud_inquisitor.utils import to_camelcase


class BaseAccount(ABC):
    class_properties = []

    """Base type object for Account objects"""
    def __init__(self, account):
        self.account = account
        self.log = logging.getLogger(self.__class__.__module__)

    def __getattr__(self, item):
        return self.get_property(item)

    def __str__(self):
        return self.account.account_name

    def get_property(self, item):
        for prop in self.account.properties:
            if prop.name == item:
                return prop

        raise AttributeError(item)

    def set_property(self, name, value):
        if type(value) == datetime:
            value = value.isoformat()
        else:
            value = value

        try:
            prop = self.get_property(name)
            if prop.value == value:
                return False

            prop.value = value

        except AttributeError:
            prop = AccountProperty()
            prop.account_id = self.id
            prop.name = name
            prop.value = value

        db.session.add(prop)

        return True

    def delete_property(self, name):
        try:
            self.log.debug('Removing property {} from {}'.format(name, self.id))
            prop = getattr(self, name)
            db.session.delete(prop)
            self.properties.remove(prop)

            return True
        except AttributeError:
            return False

    def save(self, *, auto_commit=True):
        try:
            db.session.add(self.account)
            if auto_commit:
                db.session.commit()
        except SQLAlchemyError as ex:
            self.log.exception('Failed updating account: {}'.format(ex))
            db.session.rollback()

    def delete(self, *, auto_commit=True):
        try:
            db.session.delete(self.account)
            if auto_commit:
                db.session.commit()
        except SQLAlchemyError:
            self.log.exception('Failed deleting account: {}'.format(self.id))
            db.session.rollback()

    def to_json(self, is_admin=False):
        """Returns a dict representation of the object

        Args:
            is_admin (`bool`): If true, include information about the account that should be avaiable only to admins

        Returns:
            `dict`
        """
        if is_admin:
            return {
                'accountId': self.account_id,
                'accountName': self.account_name,
                'accountType': self.account_type,
                'contacts': self.contacts,
                'enabled': True if self.enabled == 1 else False,
                'requiredRoles': self.required_roles,
                'properties': {to_camelcase(prop.name): prop.value for prop in self.account.properties}
            }
        else:
            return {
                'accountId': self.account_id,
                'accountName': self.account_name,
                'contacts': self.contacts
            }

    def update(self, **kwargs):
        """Updates the object information based on live data, if there were any changes made. Any changes will be
        automatically applied to the object, but will not be automatically persisted. You must manually call
        `db.session.add(object)` on the object.

        Args:
            **kwargs (:obj:): AWS API Resource object fetched from AWS API

        Returns:
            `bool`
        """
        updated = False

        for prop in self.class_properties:
            key = prop['key']
            kwarg_key = to_camelcase(key)
            if kwarg_key in kwargs:
                if prop['required'] and not kwargs[kwarg_key]:
                    raise InquisitorError('Missing required property {}'.format(prop['name']))

                updated |= self.set_property(key, kwargs[kwarg_key])

        return updated

    # region Object properties
    @property
    def account_id(self):
        return self.account.account_id

    @account_id.setter
    def account_id(self, value):
        self.account.account_id = value

    @property
    def account_name(self):
        return self.account.account_name

    @account_name.setter
    def account_name(self, value):
        self.account.account_name = value

    @property
    def contacts(self):
        return self.account.contacts

    @contacts.setter
    def contacts(self, value):
        self.account.contacts = value

    @property
    def enabled(self):
        return self.account.enabled

    @enabled.setter
    def enabled(self, value):
        self.account.enabled = value

    @property
    def required_roles(self):
        return self.account.required_roles

    @required_roles.setter
    def required_roles(self, value):
        self.account.required_roles = value

    @property
    def properties(self):
        return self.account.properties

    @property
    @abstractmethod
    def account_type(self):
        """Human friendly name of the account type"""
    # endregion

    # region Class and static methods
    @staticmethod
    def get(account):
        """Returns the class object identified by `account_id`

        Args:
            account (`int`, `str`): Unique ID of the account to load from database

        Returns:
            `Account` object if found, else None
        """
        account = Account.get(account)
        if not account:
            return None

        acct_type = AccountType.get(account.account_type_id).account_type
        account_class = get_plugin_by_name(PLUGIN_NAMESPACES['accounts'], acct_type)

        return account_class(account)

    @classmethod
    def create(cls, *, account_name, contacts, enabled, required_roles=list(), properties=None, auto_commit=True):
        if cls.get(account_name):
            raise AccountException('Account {} already exists'.format(account_name))

        for prop in cls.class_properties:
            if prop['required'] and (prop['key'] not in properties or not properties[prop['key']]):
                raise InquisitorError('Missing required property {}'.format(prop['name'], cls.__name__))

        res = Account()
        res.account_name = account_name
        res.contacts = contacts
        res.enabled = enabled
        res.required_roles = required_roles
        res.account_type_id = AccountType.get(cls.account_type).account_type_id

        if properties:
            for name, value in properties.items():
                prop = AccountProperty()
                prop.account_id = res.account_id
                prop.name = name
                prop.value = value.isoformat() if type(value) == datetime else value
                res.properties.append(prop)
                db.session.add(prop)

        db.session.add(res)
        if auto_commit:
            db.session.commit()

        return res

    @classmethod
    def get_all(cls, include_disabled=True):
        """Returns a list of all accounts of a given type

        Args:
            include_disabled (`bool`): Include disabled accounts. Default: `True`

        Returns:
            list of account objects
        """
        if cls == BaseAccount:
            raise InquisitorError('get_all on BaseAccount is not supported')

        account_type_id = db.AccountType.find_one(account_type=cls.account_type).account_type_id
        qry = db.Account.order_by(desc(Account.enabled), Account.account_type_id, Account.account_name)

        if not include_disabled:
            qry = qry.filter(Account.enabled == 1)

        accounts = qry.find(Account.account_type_id == account_type_id)

        return {res.account_id: cls(res) for res in accounts}

    @staticmethod
    def search(*, include_disabled=True, account_ids=None, account_type_id=None, properties=None, return_query=False):
        """Search for accounts based on the provided filters

        Args:
            include_disabled (`bool`): Include disabled accounts (default: True)
            account_ids: (`list` of `int`): List of account IDs
            account_type_id (`int`): Account Type ID to limit results to
            properties (`dict`): A `dict` containing property name and value pairs. Values can be either a str or a list
            of strings, in which case a boolean OR search is performed on the values
            return_query (`bool`): Returns the query object prior to adding the limit and offset functions. Allows for
            sub-classes to amend the search feature with extra conditions. The calling function must handle pagination
            on its own

        Returns:
            `list` of `Account`, `sqlalchemy.orm.Query`
        """
        qry = db.Account.order_by(desc(Account.enabled), Account.account_type_id, Account.account_name)

        if not include_disabled:
            qry = qry.filter(Account.enabled == 1)

        if account_ids:
            if type(account_ids) not in (list, tuple):
                account_ids = [account_ids]

            qry = qry.filter(Account.account_id.in_(account_ids))

        if account_type_id:
            qry = qry.filter(Account.account_type_id == account_type_id)

        if properties:
            for prop_name, value in properties.items():
                alias = aliased(AccountProperty)
                qry = qry.join(alias, Account.account_id == alias.account_id)
                if type(value) == list:
                    where_clause = []
                    for item in value:
                        where_clause.append(alias.value == item)

                    qry = qry.filter(
                        and_(
                            alias.name == prop_name,
                            or_(*where_clause)
                        ).self_group()
                    )
                else:
                    qry = qry.filter(
                        and_(
                            alias.name == prop_name,
                            alias.value == value
                        ).self_group()
                    )

        if return_query:
            return qry

        total = qry.count()
        return total, list(map(BaseAccount.get_typed_account, qry.all()))

    @staticmethod
    def get_typed_account(account):
        if type(account) in (int, str):
            account = Account.get(account)

        acct_type = AccountType.get(account.account_type_id).account_type
        account_class = get_plugin_by_name(PLUGIN_NAMESPACES['accounts'], acct_type)
        return account_class.get(account['account_id'])
    # endregion


class AWSAccount(BaseAccount):
    account_type = 'AWS'
    account_type_name = 'AWS Account'
    class_properties = [
        {
            'key': 'account_number',
            'type': 'string',
            'name': 'Account Number',
            'default': '',
            'required': True
        },
        {
            'key': 'ad_group_base',
            'type': 'string',
            'name': 'AD Group Base',
            'default': '',
            'required': False
        }
    ]

    # region Object properties
    @property
    def account_number(self):
        """Returns the Account Number

        Returns:
            `str`
        """
        return self.get_property('account_number').value

    @property
    def ad_group_base(self):
        """Returns the AD Group Base for the account

        Returns:
            `str`
        """
        return self.get_property('ad_group_base').value
    # endregion


class AXFRAccount(BaseAccount):
    account_type = 'DNS: AXFR'
    account_type_name = 'DNS: AXFR'
    class_properties = [
        {
            'key': 'server',
            'name': 'Server',
            'type': 'string',
            'default': '',
            'required': True
        },
        {
            'key' :'domains',
            'name': 'Domains',
            'type': 'array',
            'default': [],
            'required': True
        }
    ]

    @property
    def server(self):
        return self.get_property('server').value

    @property
    def domains(self):
        return self.get_property('domains').value


class CloudFlareAccount(BaseAccount):
    account_type = 'DNS: CloudFlare'
    account_type_name = 'DNS: CloudFlare'
    class_properties = [
        {
            'key': 'endpoint',
            'name': 'API Endpoint',
            'type': 'string',
            'default': '',
            'required': True
        },
        {
            'key': 'api_key',
            'name': 'API Key',
            'type': 'string',
            'default': '',
            'required': True
        },
        {
            'key': 'email',
            'name': 'Email',
            'type': 'string',
            'default': '',
            'required': True
        }
    ]

    @property
    def endpoint(self):
        return self.get_property('endpoint').value

    @property
    def api_key(self):
        return self.get_property('api_key').value

    @property
    def email(self):
        return self.get_property('email').value
