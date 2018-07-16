from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER as Integer, SMALLINT as SmallInteger, JSON
from sqlalchemy.orm import foreign, relationship

from cloud_inquisitor.constants import ROLE_ADMIN
from cloud_inquisitor.database import db, Model
from cloud_inquisitor.schema.base import BaseModelMixin

__all__ = ('AccountType', 'AccountProperty', 'Account')


class AccountType(Model, BaseModelMixin):
    __tablename__ = 'account_types'

    account_type_id = Column(Integer(unsigned=True), primary_key=True, autoincrement=True)
    account_type = Column(String(100), nullable=False, index=True, unique=True)

    @classmethod
    def get(cls, account_type):
        if isinstance(account_type, str):
            obj = getattr(db, cls.__name__).find_one(cls.account_type == account_type)

        elif isinstance(account_type, int):
            obj = getattr(db, cls.__name__).find_one(cls.account_type_id == account_type)

        elif isinstance(account_type, cls):
            return account_type

        else:
            obj = None

        if not obj:
            if type(account_type) == str:
                obj = cls()
                obj.account_type = account_type

                db.session.add(obj)
                db.session.commit()
                db.session.refresh(obj)
            else:
                raise ValueError('Unable to find or create a new account type: {}'.format(account_type))

        return obj


class AccountProperty(Model, BaseModelMixin):
    __tablename__ = 'account_properties'

    property_id = Column(Integer(unsigned=True), primary_key=True, autoincrement=True)
    account_id = Column(
        Integer(unsigned=True),
        ForeignKey('accounts.account_id', name='fk_account_properties_account_id', ondelete='CASCADE'),
        nullable=False,
        primary_key=True,
        index=True
    )
    name = Column(String(50), nullable=False, index=True)
    value = Column(JSON, nullable=False)

    def __str__(self):
        return self.value

    def __repr__(self):
        return "{}({}, '{}', '{}', '{}')".format(
            self.__class__.__name__,
            self.property_id,
            self.account_id,
            self.name,
            self.value
        )


class Account(Model, BaseModelMixin):
    __tablename__ = 'accounts'

    account_id = Column(Integer(unsigned=True), primary_key=True, autoincrement=True)
    account_name = Column(String(256), nullable=False, index=True, unique=True)
    account_type_id = Column(
        Integer(unsigned=True),
        ForeignKey(AccountType.account_type_id, name='fk_account_account_type_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    contacts = Column(JSON, nullable=False)
    enabled = Column(SmallInteger(unsigned=True), nullable=False, default=1)
    required_roles = Column(JSON, nullable=True)
    properties = relationship(
        'AccountProperty',
        lazy='select',
        uselist=True,
        primaryjoin=account_id == foreign(AccountProperty.account_id),
        cascade='all, delete-orphan'
    )

    @staticmethod
    def get(account_id, account_type_id=None):
        """Return account by ID and type

        Args:
            account_id (`int`, `str`): Unique Account identifier
            account_type_id (str): Type of account to get

        Returns:
            :obj:`Account`: Returns an Account object if found, else None
        """
        if type(account_id) == str:
            args = {'account_name': account_id}
        else:
            args = {'account_id': account_id}

        if account_type_id:
            args['account_type_id'] = account_type_id

        return db.Account.find_one(**args)

    def user_has_access(self, user):
        """Check if a user has access to view information for the account

        Args:
            user (:obj:`User`): User object to check

        Returns:
            True if user has access to the account, else false
        """
        if ROLE_ADMIN in user.roles:
            return True

        # Non-admin users should only see active accounts
        if self.enabled:
            if not self.required_roles:
                return True

            for role in self.required_roles:
                if role in user.roles:
                    return True

        return False
