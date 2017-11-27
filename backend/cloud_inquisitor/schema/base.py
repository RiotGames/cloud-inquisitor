import enum
from datetime import datetime
from logging import getLogger

from sqlalchemy import Column, String, DateTime, ForeignKey, SmallInteger, Text, UniqueConstraint, text, func
from sqlalchemy.dialects import mysql
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import QueryableAttribute
from sqlalchemy.orm.collections import InstrumentedList

from cloud_inquisitor import db
from cloud_inquisitor.constants import ROLE_ADMIN, SchedulerStatus, AccountTypes
from cloud_inquisitor.exceptions import SchedulerError
from cloud_inquisitor.utils import isoformat, to_camelcase

log = getLogger(__name__)
Integer = mysql.INTEGER
JSON = mysql.JSON
TinyInt = mysql.TINYINT

@as_declarative()
class BaseModelMixin(object):
    """Mixin class for db.Model object's to expose some common functionality"""
    @classmethod
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def to_json(self):
        """Exports the object to a JSON friendly dict

        Returns:
             Dict representation of object type
        """
        output = {
            '__type': self.__class__.__name__
        }

        cls_attribs = self.__class__.__dict__
        for attrName in cls_attribs:
            attr = getattr(self.__class__, attrName)
            value = getattr(self, attrName)
            value_class = type(value)

            if issubclass(type(attr), QueryableAttribute):
                # List of db.Model, BaseModelMixin objects (one-to-many relationship)
                if issubclass(value_class, InstrumentedList):
                    output[to_camelcase(attrName)] = [x.to_json() for x in value]

                # db.Model, BaseModelMixin object (one-to-one relationship)
                elif issubclass(value_class, db.Model):
                    output[to_camelcase(attrName)] = value.to_json()

                # Datetime object
                elif isinstance(value, datetime):
                    output[to_camelcase(attrName)] = isoformat(value)

                elif isinstance(value, enum.Enum):
                    output[to_camelcase(attrName)] = value.name

                # Any primitive type
                else:
                    output[to_camelcase(attrName)] = value

        return output


class Account(db.Model, BaseModelMixin):
    """Account object class

    Attributes:
        account_id (int): Unique internal ID for the account
        account_name (string): Name of the account
        account_number (int): Unique AWS provided account number
        contacts (:obj:`list` of :obj:`str`): List of contacts for the account
        ad_group_base (str): The base name of the AD Groups used for SAML federation
        enabled (bool): If True (default value) the account will be included in all collections, reports etc
        required_roles (`list` of `str`): List of roles required to see information about the account
    """
    __tablename__ = 'accounts'

    account_id = Column(Integer, primary_key=True, autoincrement=True)
    account_name = Column(String(64), nullable=False, unique=True)
    account_number = Column(String(12), nullable=False, unique=True)
    account_type = Column(String(50), nullable=False, server_default=AccountTypes.AWS)
    contacts = Column(mysql.JSON, nullable=False)
    ad_group_base = Column(String(64), nullable=True)
    enabled = Column(SmallInteger, nullable=False, default=1)
    required_roles = Column(mysql.JSON, nullable=True)

    def __init__(self, name=None, account_number=None, contacts=None, enabled=True, ad_group_base=None):
        """

        Args:
            name (str): Name of the account
            account_number (int): Unique account identifier
            contacts (:obj:`list` of :obj:`str`): List of contacts for the account
            enabled (bool): If True (default value) the account will be included in all collections, reports etc.
            ad_group_base (str): The base name of the AD Groups used for SAML federation
        """
        self.account_name = name
        self.account_number = account_number
        self.contacts = contacts
        self.ad_group_base = ad_group_base
        self.enabled = 1 if enabled else 0
        self.required_roles = []

    def __str__(self):
        return self.account_name

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
                'accountNumber': self.account_number,
                'accountType': self.account_type,
                'contacts': self.contacts,
                'adGroupBase': self.ad_group_base,
                'enabled': True if self.enabled == 1 else False,
                'requiredRoles': self.required_roles
            }
        else:
            return {
                'accountId': self.account_id,
                'accountName': self.account_name,
                'contacts': self.contacts
            }

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
            if not self.required_roles or len(self.required_roles) == 0:
                return True

            for role in self.required_roles:
                if role in user.roles:
                    return True

        return False

    @classmethod
    def get(cls, account):
        """Return an Account object by name

        Args:
            account (str): Name of the account to lookup

        Returns:
            Account object or None if not found
        """
        if isinstance(account, str):
            return cls.query.filter_by(account_name=account).first()

        elif isinstance(account, int):
            return cls.query.filter_by(account_number=account).first()

        elif isinstance(account, cls):
            return account

        else:
            return None

    @classmethod
    def get_by_id(cls, account_id):
        """Returns an Account object based on the account_id

        Args:
            account_id (int): ID of the account to fetch

        Returns:
            :obj:`Account`
        """
        return cls.query.filter_by(account_id=account_id).first()


class Tag(db.Model, BaseModelMixin):
    """Tag object

    Attributes:
        tag_id (int): Internal unique ID for the object
        resource_id (str): ID of the resource the tag is associated with
        key (str): Key of the tag
        value (str): Value of the tag
        created (datetime): The first time this tag was defined
    """
    __tablename__ = 'tags'
    __table_args__ = (
        UniqueConstraint('tag_id', 'key', 'resource_id', name='uniq_tag_resource_id_key'),
    )

    tag_id = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(String(256), index=True, primary_key=True)
    key = Column(String(128), nullable=False, primary_key=True)
    value = Column(String(256), nullable=False, index=True)
    created = Column(DateTime, nullable=False)

    def __init__(self, resource_id=None, key=None, value=None):
        self.resource_id = resource_id
        self.key = key
        self.value = value
        self.created = datetime.now()

    def __str__(self):
        return '{0} = {1}'.format(self.key, self.value)

    def __repr__(self):
        return "Tag(tag_id={}, resource_id='{}', key='{}', value='{}', created='{}')".format(
            self.tag_id,
            self.resource_id,
            self.key,
            self.value,
            self.created
        )


class LogEvent(db.Model, BaseModelMixin):
    """Log Event object

    Attributes:
        log_event_id (int): Internal unique ID
        level (str): Log level name
        levelno (int): Numeric log level
        timestamp (datetime): Timestamp for log event
        message (str):
        module (str):
        filename (str):
        lineno (int):
        funcname (str):
        pathname (str):
        process_id (int):
        stacktrace (str):
    """
    __tablename__ = 'logs'

    log_event_id = Column(Integer, autoincrement=True, primary_key=True)
    level = Column(String(10), nullable=False, index=True)
    levelno = Column(SmallInteger, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    message = Column(Text, nullable=False)
    module = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    lineno = Column(Integer, nullable=True)
    funcname = Column(String(255), nullable=False)
    pathname = Column(Text, nullable=True)
    process_id = Column(Integer, nullable=True)
    stacktrace = Column(Text, nullable=True)


class Email(db.Model, BaseModelMixin):
    """Email object

    Attributes:
        email_id (int): Internal unique ID
        timestamp (datetime): Timestamp when the email was sent
        subsystem (str): Subsystem that sent the email
        subject (str): Subject line
        sender (str): Email address of the sender
        recipients (`list` of `str`): List of recipients
        uuid (str): Unique ID for the message (for tracking purposes)
        message_html (str): HTML formatted message
        message_text (str): Text formatted message
    """
    __tablename__ = 'emails'

    email_id = Column(Integer, autoincrement=True, primary_key=True)
    timestamp = Column(mysql.DATETIME, nullable=False, index=True)
    subsystem = Column(String(64), nullable=False, index=True)
    subject = Column(String(256), nullable=False)
    sender = Column(String(256), nullable=False)
    recipients = Column(mysql.JSON, nullable=False)
    uuid = Column(String(36), nullable=False, index=True)
    message_html = Column(mysql.TEXT)
    message_text = Column(mysql.TEXT)

    def to_json(self, include_body=False):
        """Exports the object to a JSON friendly dict

        Args:
            include_body (bool): Include the body of the message in the output

        Returns:
             Dict representation of object type
        """

        message = {
            'emailId': self.email_id,
            'timestamp': isoformat(self.timestamp),
            'subsystem': self.subsystem,
            'subject': self.subject,
            'sender': self.sender,
            'recipients': self.recipients,
            'uuid': self.uuid,
            'messageHtml': None,
            'messageText': None
        }

        if include_body:
            message['messageHtml'] = self.message_html
            message['messageText'] = self.message_text

        return message


class ConfigNamespace(db.Model, BaseModelMixin):
    """Configuration Namespace object

    Attributes:
        namespace_prefix (str): Unique namespace prefix
        name (str): Human-friendly name
        sort_order (int): Sorting value
        config_items (`list` of :obj:`ConfigItem`): List of configuration items for the namespace
    """
    __tablename__ = 'config_namespaces'

    namespace_prefix = Column(String(100), primary_key=True, nullable=False)
    name = Column(String(100), nullable=False)
    sort_order = Column(SmallInteger, server_default='2', nullable=False)
    config_items = relationship(
        'ConfigItem',
        lazy='subquery',
        cascade='all,delete',
        order_by='ConfigItem.key'
    )


class ConfigItem(db.Model, BaseModelMixin):
    """Configuration Item object

    Attributes:
        config_item_id (int): Internal unique ID
        key (str): Name / key of the item
        value (str): Value of the config item
        type (str): Type of configuration object (string, int, float, array, json)
        namespace_prefix (str): Namespace the item is under
        description (str): Brief description of the uses of the config item
    """
    __tablename__ = 'config_items'
    __table_args__ = (
        UniqueConstraint('key', 'namespace_prefix', name='uniq_key_namespace'),
    )

    config_item_id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(256), nullable=False, index=True)
    value = Column(mysql.JSON, nullable=False)
    type = Column(String(20), nullable=False, default='string')
    namespace_prefix = Column(
        String(100),
        ForeignKey(ConfigNamespace.namespace_prefix, name='fk_config_namespace_prefix', ondelete='CASCADE'),
        nullable=False,
        server_default='default'
    )
    description = Column(String(256), nullable=True, default=None)

    @classmethod
    def get(cls, ns, key):
        """Fetch an item by namespace and key

        Args:
            ns (str): Namespace prefix
            key (str): Item key

        Returns:
            :obj:`Configitem`: Returns config item object if found, else `None`
        """
        return (cls.query
            .filter(ConfigItem.namespace_prefix == ns)
            .filter(ConfigItem.key == key)
            .first()
        )


class Role(db.Model, BaseModelMixin):
    """User role object

    Attributes:
        role_id (int): Internal unique ID
        name (str): Name of the role
        color (str): Color used in frontend to distinguish roles at a glance
    """
    __tablename__ = 'roles'

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    color = Column(String(7), nullable=False, server_default='#9E9E9E')

    def __str__(self):
        return self.name

    def __cmp__(self, other):
        return self.name.lower() == other.name.lower()

    def __eq__(self, other):
        if isinstance(other, Role):
            return self.name.lower() == other.name.lower()
        elif isinstance(other, str):
            return self.name.lower() == other.lower()
        else:
            raise NotImplementedError('Invalid type comparison')

    def __hash__(self):
        return hash(self.name)

    @staticmethod
    def get(name):
        """Returns a role object by name if found, else None

        Args:
            name (str): Name of the role to get

        Returns:
            `Role`,`None`
        """
        return Role.query.filter_by(name=name).first()

    @classmethod
    def from_json(cls, data):
        """Return object based on JSON / dict input

        Args:
            data (dict): Dictionary containing a serialized Role object

        Returns:
            :obj:`Role`: Role object representing the data
        """
        role = cls()

        role.role_id = data['roleId']
        role.name = data['name']
        role.color = data['color']

        return role


class User(db.Model, BaseModelMixin):
    """User object

    Attributes:
        user_id (int): Internal unique ID
        username (str): Username
        password (str): Argon2 hashed password
        auth_system (str): Auth System that created the user
        roles (`list` of :obj:`Role`): List of roles applied to the user
    """
    __tablename__ = 'users'
    __table_args__ = (
        UniqueConstraint('username', 'auth_system', name='uniq_username_authsys'),
    )

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    password = Column(String(73), nullable=True)
    auth_system = Column(String(50), nullable=False, server_default='builtin')
    roles = relationship(
        'Role',
        uselist=True,
        lazy='joined',
        secondary='user_roles',
        order_by=Role.role_id)

    def get_accounts(self):
        """Get a list of accounts the user has access to

        Returns:
            `list` of :obj:`Account`: List of accounts the user has access to
        """
        accounts = Account.query.all()

        if 'Admin' in self.roles:
            return accounts

    def __str__(self):
        return '<User username={}, AuthSystem: {}, Roles: {}>'.format(
            self.username,
            self.auth_system,
            ', '.join([x.name for x in self.roles])
        )

    @staticmethod
    def add_role(user, roles):
        """Map roles for user in database

        Args:
            user (User): User to add roles to
            roles ([Role]): List of roles to add

        Returns:
            None
        """
        def _add_role(role):
            user_role = UserRole()
            user_role.user_id = user.user_id
            user_role.role_id = role.role_id
            db.session.add(user_role)
            db.session.commit()
        [_add_role(role) for role in roles]

    @classmethod
    def from_json(cls, data):
        """Return object based on JSON / dict input

        Args:
            data (dict): Dictionary containing a serialized User object

        Returns:
            :obj:`User`: User object representing the data
        """
        user = cls()

        user.user_id = data['userId']
        user.username = data['username']
        user.auth_system = data['authSystem']
        user.roles = data['roles']

        return user

    def to_json(self):
        """Exports the object to a JSON friendly dict

        Returns:
            Dict representation of the object
        """
        return {
            'userId': self.user_id,
            'username': self.username,
            'roles': self.roles,
            'authSystem': self.auth_system
        }


class UserRole(db.Model, BaseModelMixin):
    """User to role mapping object

    Warnings:
        This object should never be accessed directly, it should only be updated by SQLAlchemy

    Attributes:
        user_role_id (int): Internal unique ID
        user_id (int): ID of the user
        role_id (int): ID of the role
    """
    __tablename__ = 'user_roles'

    user_role_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.user_id, name='fk_user_role_user', ondelete='CASCADE'))
    role_id = Column(Integer, ForeignKey(Role.role_id, name='fk_user_role_role', ondelete='CASCADE'))


class AuditLog(db.Model, BaseModelMixin):
    """Audit Log Event

    Attributes:
        audit_log_event_id (int): Internal unique ID
        timestamp (datetime): Timestamp for the event
        actor (str): Actor (user or subsystem) triggering the event
        event (str): Action performed
        data (dict): Any extra data necessary for describing the event
    """
    __tablename__ = 'auditlog'

    audit_log_event_id = Column(Integer(unsigned=True), autoincrement=True, primary_key=True)
    timestamp = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    actor = Column(String(100), nullable=False, index=True)
    event = Column(String(50), nullable=False, index=True)
    data = Column(mysql.JSON, nullable=False)

    @classmethod
    def log(cls, event=None, actor=None, data=None):
        """Generate and insert a new event

        Args:
            event (str): Action performed
            actor (str): Actor (user or subsystem) triggering the event
            data (dict): Any extra data necessary for describing the event

        Returns:
            `None`
        """
        try:
            entry = cls()
            entry.event = event
            entry.actor = actor
            entry.data = data

            db.session.add(entry)
            db.session.commit()

        except Exception:
            log.exception('Failed adding audit log event')
            db.session.rollback()


class SchedulerBatch(db.Model, BaseModelMixin):
    __tablename__ = 'scheduler_batches'

    batch_id = Column(String(36), primary_key=True)
    status = Column(TinyInt, default=0, nullable=False, index=True)
    started = Column(DateTime, server_default=func.now(), nullable=False)
    completed = Column(DateTime, nullable=True)

    jobs = relationship(
        'SchedulerJob',
        lazy='subquery',
        cascade='all,delete'
    )

    def update_status(self, new_status):
        if self.status == SchedulerStatus.COMPLETED:
            raise SchedulerError('Attempting to update already completed batch')

        if new_status > self.status:
            self.status = new_status
            if self.status >= SchedulerStatus.COMPLETED:
                self.completed = datetime.now()

            db.session.add(self)
            return True

        return False

    @staticmethod
    def get(batch_id):
        return SchedulerBatch.query.filter_by(batch_id=batch_id).first()


class SchedulerJob(db.Model, BaseModelMixin):
    __tablename__ = 'scheduler_jobs'

    job_id = Column(String(36), primary_key=True)
    batch_id = Column(
        String(36),
        ForeignKey(SchedulerBatch.batch_id, name='fk_scheduler_job_batch_id', ondelete='CASCADE'),
        nullable=False
    )
    status = Column(TinyInt, default=0, nullable=False, index=True)
    data = Column(JSON, nullable=False)

    def update_status(self, new_status):
        if self.status == SchedulerStatus.COMPLETED:
            raise SchedulerError('Attempting to update already completed job')

        if new_status > self.status:
            self.status = new_status
            db.session.add(self)

            return True

        return False

    @staticmethod
    def get(job_id):
        return SchedulerJob.query.filter_by(job_id=job_id).first()
