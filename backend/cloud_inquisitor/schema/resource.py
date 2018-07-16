from datetime import datetime

from sqlalchemy import Column, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.mysql import INTEGER as Integer, JSON
from sqlalchemy.orm import foreign, relationship

from cloud_inquisitor.database import db, Model
from cloud_inquisitor.schema import Account
from cloud_inquisitor.schema.base import BaseModelMixin

__all__ = ('Tag', 'ResourceType', 'ResourceProperty', 'Resource', 'ResourceMapping')


class Tag(Model, BaseModelMixin):
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
    resource_id = Column(
        String(256),
        ForeignKey('resources.resource_id', name='fk_tag_resource_id', ondelete='CASCADE'),
        index=True,
        primary_key=True
    )
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


class ResourceType(Model, BaseModelMixin):
    """Resource type object

    Attributes:
        resource_type_id (int): Unique resource type identifier
        resource_type (str): Resource type name
    """
    __tablename__ = 'resource_types'

    resource_type_id = Column(Integer(unsigned=True), primary_key=True, autoincrement=True)
    resource_type = Column(String(100), nullable=False, index=True)

    @classmethod
    def get(cls, resource_type):
        """Returns the ResourceType object for `resource_type`. If no existing object was found, a new type will
        be created in the database and returned

        Args:
            resource_type (str): Resource type name

        Returns:
            :obj:`ResourceType`
        """
        if isinstance(resource_type, str):
            obj = getattr(db, cls.__name__).find_one(cls.resource_type == resource_type)

        elif isinstance(resource_type, int):
            obj = getattr(db, cls.__name__).find_one(cls.resource_type_id == resource_type)

        elif isinstance(resource_type, cls):
            return resource_type

        else:
            obj = None

        if not obj:
            obj = cls()
            obj.resource_type = resource_type
            db.session.add(obj)
            db.session.commit()
            db.session.refresh(obj)

        return obj


class ResourceProperty(Model, BaseModelMixin):
    """Resource Property object"""
    __tablename__ = 'resource_properties'

    property_id = Column(Integer(unsigned=True), primary_key=True, autoincrement=True)
    resource_id = Column(
        String(256),
        ForeignKey('resources.resource_id', name='fk_resource_property_resource_id', ondelete='CASCADE'),
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
            self.resource_id,
            self.name,
            self.value
        )


class Resource(Model, BaseModelMixin):
    """Resource object

    Attributes:
        resource_id (`str`): Unique Resource identifier
        account_id (`int`): ID of the account owning the resource
        location (`str`, optional): Optional location of the resource (eg. aws region)
        resource_type (`str`): :obj:`ResourceType` reference
        tags (`list` of :obj:`Tag`): List of tags applied to the volume
        properties (`list` of :obj:`ResourceProperty`): List of properties of the resource
    """
    __tablename__ = 'resources'

    resource_id = Column(String(256), primary_key=True)
    account_id = Column(
        Integer(unsigned=True),
        ForeignKey('accounts.account_id', name='fk_resource_account_id', ondelete='CASCADE'),
        index=True
    )
    location = Column(String(50), nullable=True, index=True)
    resource_type_id = Column(
        Integer(unsigned=True),
        ForeignKey('resource_types.resource_type_id', name='fk_resource_types_resource_type_id', ondelete='CASCADE'),
        index=True
    )
    tags = relationship(
        'Tag',
        lazy='select',
        uselist=True,
        primaryjoin=resource_id == foreign(Tag.resource_id),
        order_by=Tag.key,
        cascade='all, delete-orphan'
    )
    properties = relationship(
        'ResourceProperty',
        lazy='select',
        uselist=True,
        primaryjoin=resource_id == foreign(ResourceProperty.resource_id),
        cascade='all, delete-orphan'
    )
    account = relationship(
        'Account',
        lazy='joined',
        uselist=False,
        primaryjoin=account_id == foreign(Account.account_id),
        viewonly=True
    )
    children = relationship(
        'Resource',
        lazy='select',
        uselist=True,
        secondary='resource_mappings',
        primaryjoin='Resource.resource_id == ResourceMapping.parent',
        secondaryjoin='Resource.resource_id == ResourceMapping.child',
        cascade='all, delete',
        backref='parents'
    )

    @staticmethod
    def get(resource_id):
        """Return resource by ID

        Args:
            resource_id (str): Unique Resource identifier

        Returns:
            :obj:`Resource`: Returns Resource object if found, else None
        """
        return db.Resource.find_one(
            Resource.resource_id == resource_id
        )

    def __repr__(self):
        return '<Resource({})>'.format(self.resource_id)


class ResourceMapping(Model, BaseModelMixin):
    """Mapping resource relationships (parent/child)

    Warnings:
        This object should never be accessed directly, it should only be updated by SQLAlchemy

    Attributes:
        id (int): Internal unique ID
        parent (int): ID of the parent object
        child (int): ID of the child object
    """
    __tablename__ = 'resource_mappings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent = Column(
        String(256),
        ForeignKey('resources.resource_id', name='fk_resource_mapping_parent', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    child = Column(
        String(256),
        ForeignKey('resources.resource_id', name='fk_resource_mapping_child', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
