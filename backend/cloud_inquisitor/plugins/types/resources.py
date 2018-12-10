import logging
import re
from abc import abstractmethod, ABC
from collections import namedtuple
from datetime import datetime, timedelta

from botocore.exceptions import ClientError
from flask import session
from sqlalchemy import func, or_, and_, cast, DATETIME
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased

from cloud_inquisitor import get_plugin_by_name
from cloud_inquisitor.constants import RGX_EMAIL_VALIDATION_PATTERN, PLUGIN_NAMESPACES
from cloud_inquisitor.database import db
from cloud_inquisitor.exceptions import ResourceException, InquisitorError
from cloud_inquisitor.schema import Tag, Account, Resource, ResourceType, ResourceProperty, ResourceMapping
from cloud_inquisitor.utils import (
    to_utc_date,
    is_truthy,
    to_camelcase,
    NotificationContact,
    parse_date,
    deprecated
)


ResourceProp = namedtuple('ResourceProp', ('key', 'name', 'type', 'show'))


class BaseResource(ABC):
    """Base type object for resource objects"""
    resource_properties = []

    def __init__(self, resource):
        self.resource = resource
        self.log = logging.getLogger(self.__class__.__module__)

    def __getattr__(self, item):
        for prop in self.resource_properties:
            if prop.key == item:
                if prop.type == 'datetime':
                    return parse_date(self.get_property(item).value)

                elif prop.type == 'bool':
                    return is_truthy(self.get_property(item).value)

                return self.get_property(item).value

        raise AttributeError('{} has no attribute {}'.format(self.__class__.__name__, item))

    def __str__(self):
        return '<{} resource_id={}>'.format(self.__class__.__name__, self.id)

    # region Object properties
    @property
    def id(self):
        return self.resource.resource_id

    @property
    def tags(self):
        return self.resource.tags

    @property
    def properties(self):
        return self.resource.properties

    @property
    def account_id(self):
        """Returns the ID of the account that owns the resource

        Returns:
            `int`
        """
        return self.resource.account_id

    @property
    def account(self):
        """Return the Account object for the instance

        Returns:
            `Account`
        """
        return self.resource.account

    @property
    def location(self):
        """Returns the location of the resource, or None

        Returns:
            `str`, `None`
        """
        return self.resource.location

    @property
    def parents(self):
        """Returns a list of parent objects (objects which the resource is attached to) if any, else `None`

        Returns:
            `list` of :obj:`Resource`, `None`
        """
        return self.resource.parents

    @property
    def children(self):
        """Returns a list of child objects (objects which are attached to the resource) if any, else `None`

        Returns:
            `list` of :obj:`Resource`, `None`
        """
        return self.resource.children

    @property
    @abstractmethod
    def resource_type(self):
        """The ResourceType of the object"""

    @property
    @abstractmethod
    def resource_name(self):
        """Human friendly name of the resource type"""

    # endregion

    # region Static and Class methods
    @abstractmethod
    def update(self, data):
        """Updates the resource object with the information from `data`. The changes will be added to the current
        db.session but will not be commited. The user will need to perform the commit explicitly to save the changes

        Args:
            data: A data object, specific to the resource

        Returns:
            True if resource object was updated, else False
        """

    @staticmethod
    def get(resource_id):
        """Returns the class object identified by `resource_id`

        Args:
            resource_id (str): Unique EC2 Instance ID to load from database

        Returns:
            EC2 Instance object if found, else None
        """
        resource = Resource.get(resource_id)

        if not resource:
            return None

        resource_type = ResourceType.get(resource.resource_type_id).resource_type
        resource_class = get_plugin_by_name(PLUGIN_NAMESPACES['types'], resource_type)

        return resource_class(resource)

    @classmethod
    def create(cls, resource_id, *, account_id, properties=None, tags=None, location=None,
               auto_add=True, auto_commit=False):
        """Creates a new Resource object with the properties and tags provided

        Args:
            resource_id (str): Unique identifier for the resource object
            account_id (int): Account ID which owns the resource
            properties (dict): Dictionary of properties for the resource object.
            tags (dict): Key / value dictionary of tags. Values must be `str` types
            location (str): Location of the resource, if applicable
            auto_add (bool): Automatically add the new resource to the DB session. Default: True
            auto_commit (bool): Automatically commit the change to the database. Default: False
        """
        if cls.get(resource_id):
            raise ResourceException('Resource {} already exists'.format(resource_id))

        res = Resource()
        res.resource_id = resource_id
        res.account_id = account_id
        res.location = location
        res.resource_type_id = ResourceType.get(cls.resource_type).resource_type_id

        if properties:
            for name, value in properties.items():
                prop = ResourceProperty()
                prop.resource_id = res.resource_id
                prop.name = name
                prop.value = value.isoformat() if type(value) == datetime else value
                res.properties.append(prop)
                db.session.add(prop)

        if tags:
            for key, value in tags.items():
                if type(value) != str:
                    raise ValueError('Invalid object type for tag value: {}'.format(key))

                tag = Tag()
                tag.resource_id = resource_id
                tag.key = key
                tag.value = value
                res.tags.append(tag)
                db.session.add(tag)

        if auto_add:
            db.session.add(res)

            if auto_commit:
                db.session.commit()

            return cls.get(res.resource_id)
        else:
            return cls(res)

    @classmethod
    def get_all(cls, account=None, location=None, include_disabled=False):
        """Returns a list of all resources for a given account, location and resource type.

        Attributes:
            account (:obj:`Account`): Account owning the resources
            location (`str`): Location of the resources to return (region)
            include_disabled (`bool`): Include resources from disabled accounts (default: False)

        Returns:
            list of resource objects
        """
        if cls == BaseResource:
            raise InquisitorError('get_all on BaseResource is not supported')

        qry = db.Resource.filter(
            Resource.resource_type_id == ResourceType.get(cls.resource_type).resource_type_id
        )

        if account:
            qry = qry.filter(Resource.account_id == account.account_id)

        if not include_disabled:
            qry = qry.join(Account, Resource.account_id == Account.account_id).filter(Account.enabled == 1)

        if location:
            qry = qry.filter(Resource.location == location)

        return {res.resource_id: cls(res) for res in qry.all()}

    @classmethod
    @deprecated('The `search` method is deprecated, please use the `find` function instead')
    def search(cls, *, limit=100, page=1, accounts=None, locations=None, resources=None,
               properties=None, include_disabled=False, return_query=False):
        """Search for resources based on the provided filters. If `return_query` a sub-class of `sqlalchemy.orm.Query`
        is returned instead of the resource list.

        Args:
            limit (`int`): Number of results to return. Default: 100
            page (`int`): Pagination offset for results. Default: 1
            accounts (`list` of `int`): A list of account id's to limit the returned resources to
            locations (`list` of `str`): A list of locations as strings to limit the search for
            resources ('list' of `str`): A list of resource_ids
            properties (`dict`): A `dict` containing property name and value pairs. Values can be either a str or a list
            of strings, in which case a boolean OR search is performed on the values
            include_disabled (`bool`): Include resources from disabled accounts. Default: False
            return_query (`bool`): Returns the query object prior to adding the limit and offset functions. Allows for
            sub-classes to amend the search feature with extra conditions. The calling function must handle pagination
            on its own

        Returns:
            `list` of `Resource`, `sqlalchemy.orm.Query`
        """
        qry = db.Resource.order_by(Resource.resource_id).filter(
            Resource.resource_type_id == ResourceType.get(cls.resource_type).resource_type_id
        )

        if not include_disabled:
            qry = qry.join(Account, Resource.account_id == Account.account_id).filter(Account.enabled == 1)

        if session:
            qry = qry.filter(Resource.account_id.in_(session['accounts']))

        if accounts:
            qry = qry.filter(Resource.account_id.in_([Account.get(acct).account_id for acct in accounts]))

        if locations:
            qry = qry.filter(Resource.location.in_(locations))

        if resources:
            qry = qry.filter(Resource.resource_id.in_(resources))

        if properties:
            for prop_name, value in properties.items():
                alias = aliased(ResourceProperty)

                qry = qry.join(alias, Resource.resource_id == alias.resource_id)

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
        qry = qry.limit(limit)
        qry = qry.offset((page - 1) * limit if page > 1 else 0)

        return total, [cls(x) for x in qry.all()]

    @classmethod
    def find(cls, *, limit=100, page=0, accounts=None, locations=None, resources=None,
             resource_types=None, parent_id=None, properties=None, include_disabled=False, return_query=False):
        """Find resources based on the provided filters.

        If `return_query` a sub-class of `sqlalchemy.orm.Query` is returned instead of the resource list.

        Args:
            limit (`int`): Number of results to return. Default: 100
            page (`int`): Pagination offset for results. Default: 0
            accounts (`list` of `int`): A list of account id's to limit the returned resources to
            locations (`list` of `str`): A list of locations as strings to limit the search for
            resources ('list' of `str`): A list of resource_ids
            resource_types (`list` of `str`): A list of resource types
            parent_id (`str`): ID of parent resource. If set, only return child objects of `parent_id`
            properties (`dict`): A `dict` containing property name and value pairs. Values can be either a str or a list
            of strings, in which case a boolean OR search is performed on the values
            include_disabled (`bool`): Include resources from disabled accounts. Default: False
            return_query (`bool`): Returns the query object prior to adding the limit and offset functions. Allows for
            sub-classes to amend the search feature with extra conditions. The calling function must handle pagination
            on its own

        Returns:
            `list` of `Resource`, `sqlalchemy.orm.Query`
        """
        qry = db.Resource.order_by(Resource.resource_type_id, Resource.resource_id)

        if cls != BaseResource or resource_types:
            qry = qry.join(
                ResourceType, Resource.resource_type_id == ResourceType.resource_type_id
            ).filter(
                ResourceType.resource_type.in_(resource_types or [cls.resource_type])
            )

        if session:
            qry = qry.filter(Resource.account_id.in_(session['accounts']))

        if not include_disabled:
            qry = qry.join(Account, Resource.account_id == Account.account_id).filter(Account.enabled == 1)

        if accounts:
            qry = qry.filter(Resource.account_id.in_([Account.get(acct).account_id for acct in accounts]))

        if locations:
            qry = qry.filter(Resource.location.in_(locations))

        if resources:
            qry = qry.filter(Resource.resource_id.in_(resources))

        if parent_id:
            qry = qry.join(ResourceMapping, Resource.resource_id == ResourceMapping.child).filter(
                ResourceMapping.parent == parent_id
            )

        if properties:
            for prop_name, value in properties.items():
                alias = aliased(ResourceProperty)

                qry = qry.join(alias, Resource.resource_id == alias.resource_id)

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
        qry = qry.limit(limit)
        qry = qry.offset(page * limit if page > 0 else 0)

        return total, list(map(BaseResource.get_typed_resource, qry.all()))

    @staticmethod
    def get_typed_resource(resource):
        """Returns a given resource object as the proper type

        Args:
             resource (BaseResource, str, int): A resource object

        Returns:
            `resource`
        """
        if type(resource) in (int, str):
            resource = Resource.get(resource)

        elif issubclass(resource.__class__, BaseResource):
            resource = resource.resource

        resource_type = ResourceType.get(resource.resource_type_id).resource_type
        resource_class = get_plugin_by_name(PLUGIN_NAMESPACES['types'], resource_type)
        if not resource_class:
            raise InquisitorError('Unknown resource type: {}'.format(resource_type))

        return resource_class(resource)

    # endregion

    # region Instance methods
    def get_owner_emails(self, partial_owner_match=True):
        """Return a list of email addresses associated with the instance, based on tags

        Returns:
            List of email addresses if any, else None
        """
        for tag in self.tags:
            if tag.key.lower() == 'owner':
                rgx = re.compile(RGX_EMAIL_VALIDATION_PATTERN, re.I)
                if partial_owner_match:
                    match = rgx.findall(tag.value)
                    if match:
                        return [NotificationContact('email', email) for email in match]
                else:
                    match = rgx.match(tag.value)
                    if match:
                        return [NotificationContact('email', email) for email in match.groups()]
        return None

    def get_name_or_id(self, with_id=False):
        """Return the value of the Name tag if present, else return the resource id

        Args:
            with_id (`bool`): Return the ID along with the name

        Returns:
            `str`
        """
        name = self.get_tag('Name')
        if name and len(name.value.strip()) > 0:
            return '{0} ({1})'.format(name.value, self.id) if with_id else name.value

        return self.id

    def get_property(self, name):
        """Return a named property for a resource, if available. Will raise an `AttributeError` if the property
        does not exist

        Args:
            name (str): Name of the property to return

        Returns:
            `ResourceProperty`
        """
        for prop in self.resource.properties:
            if prop.name == name:
                return prop

        raise AttributeError(name)

    def set_property(self, name, value):
        """Create or set the value of a property. Returns `True` if the property was created or updated, or `False` if
        there were no changes to the value of the property.

        Args:
            name (str): Name of the property to create or update
            value (any): Value of the property. This can be any type of JSON serializable data

        Returns:
            `bool`
        """
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
            prop = ResourceProperty()
            prop.resource_id = self.id
            prop.name = name
            prop.value = value

        db.session.add(prop)

        return True

    def delete_property(self, name):
        """Removes a property from an object, by the name of the property. Returns `True` if the property was removed or
        `False` if the property didn't exist.

        Args:
            name (str): Name of the property to delete

        Returns:
            `bool`
        """
        try:
            self.log.debug('Removing property {} from {}'.format(name, self.id))
            prop = getattr(self, name)
            self.properties.remove(prop)

            db.session.delete(prop)

            return True
        except AttributeError:
            return False

    def get_tag(self, key, *, case_sensitive=True):
        """Return a tag by key, if found

        Args:
            key (str): Name/key of the tag to locate
            case_sensitive (bool): Should tag keys be treated case-sensitive (default: true)

        Returns:
            `Tag`,`None`
        """
        key = key if case_sensitive else key.lower()
        for tag in self.resource.tags:
            if not case_sensitive:
                if tag.key.lower() == key:
                    return tag
            elif key == tag.key:
                return tag

        return None

    def set_tag(self, key, value, update_session=True):
        """Create or set the value of the tag with `key` to `value`. Returns `True` if the tag was created or updated or
        `False` if there were no changes to be made.

        Args:
            key (str): Key of the tag
            value (str): Value of the tag
            update_session (bool): Automatically add the change to the SQLAlchemy session. Default: True

        Returns:
            `bool`
        """
        existing_tags = {x.key: x for x in self.tags}
        if key in existing_tags:
            tag = existing_tags[key]

            if tag.value == value:
                return False

            tag.value = value
        else:
            tag = Tag()
            tag.resource_id = self.id
            tag.key = key
            tag.value = value
            self.tags.append(tag)

        if update_session:
            db.session.add(tag)
        return True

    def delete_tag(self, key, update_session=True):
        """Removes a tag from a resource based on the tag key. Returns `True` if the tag was removed or `False` if the
        tag didn't exist

        Args:
            key (str): Key of the tag to delete
            update_session (bool): Automatically add the change to the SQLAlchemy session. Default: True

        Returns:

        """
        existing_tags = {x.key: x for x in self.tags}
        if key in existing_tags:
            if update_session:
                db.session.delete(existing_tags[key])

            self.tags.remove(existing_tags[key])
            return True

        return False

    def save(self, *, auto_commit=False):
        """Save the resource to the database

        Args:
            auto_commit (bool): Automatically commit the transaction. Default: `False`

        Returns:
            `None`
        """
        try:
            db.session.add(self.resource)
            if auto_commit:
                db.session.commit()
        except SQLAlchemyError as ex:
            self.log.exception('Failed updating resource: {}'.format(ex))
            db.session.rollback()

    def delete(self, *, auto_commit=False):
        """Removes a resource from the database

        Args:
            auto_commit (bool): Automatically commit the transaction. Default: `False`

        Returns:
            `None`
        """
        try:
            db.session.delete(self.resource)
            if auto_commit:
                db.session.commit()
        except SQLAlchemyError:
            self.log.exception('Failed deleting resource: {}'.format(self.id))
            db.session.rollback()

    def update_resource(self, properties, tags=None):
        """Updates the resource object with the information from `data`. The changes will be added to the current
        db.session but will not be commited. The user will need to perform the commit explicitly to save the changes

        Args:
            properties (`dict`): A dictionary of properties to update
            tags (`dict`): A dictionary of tags to update

        Returns:
            True if resource object was updated, else False
        """
        updated = False

        for prop in self.resource_properties:
            key = prop.key
            if key in properties:
                updated |= self.set_property(key, properties[key])

        if tags is not None:
            existing_tags = {x.key: x for x in self.tags}
            for key, value in list(tags.items()):
                updated |= self.set_tag(key, value)

            # Check for removed tags
            for key in list(existing_tags.keys()):
                if key not in tags:
                    updated |= self.delete_tag(key)

        return updated

    def add_child(self, child):
        """Add a new child object to the resource

        Args:
            child (`BaseResource`): Child resource object

        Returns:
            `None`
        """
        self.children.append(child.resource)

    def delete_child(self, child):
        """Remove a child from the object

        Args:
            child (`BaseResource`): Child resource object

        Returns:
            `None`
        """
        self.children.remove(child.resource)
        child.delete()

    def to_json(self, with_children=False):
        """Return a `dict` representation of the resource, including all properties and tags

        Args:
            with_children (`bool`): Return any child resource objects along with the data

        Returns:
            `dict`
        """
        res = {
            'resourceType': self.resource.resource_type_id,
            'resourceId': self.id,
            'accountId': self.resource.account_id,
            'account': self.account,
            'location': self.resource.location,
            'properties': {to_camelcase(prop.name): prop.value for prop in self.resource.properties},
            'tags': [{'key': t.key, 'value': t.value} for t in self.resource.tags]
        }

        if with_children:
            res['children'] = self.children

        return res
    # endregion


class EC2Instance(BaseResource):
    """EC2 Instance"""
    resource_type = 'aws_ec2_instance'
    resource_name = 'EC2 Instance'
    resource_properties = [
        ResourceProp(key='launch_date', name='Launch Date', type='datetime', show=True),
        ResourceProp(key='state', name='State', type='string', show=True),
        ResourceProp(key='instance_type', name='Instance Type', type='string', show=True),
        ResourceProp(key='public_ip', name='Public IP', type='string', show=True),
        ResourceProp(key='public_dns', name='Public DNS', type='string', show=True),
        ResourceProp(key='created', name='Created', type='datetime', show=False),
    ]

    # region Object properties
    @property
    def resource_creation_date(self):
        return self.launch_date

    @property
    def volumes(self):
        """Returns a list of the volumes attached to the instance

        Returns:
            `list` of `EBSVolume`
        """
        return [
            EBSVolume(res) for res in db.Resource.join(
                ResourceProperty, Resource.resource_id == ResourceProperty.resource_id
            ).filter(
                Resource.resource_type_id == ResourceType.get(EBSVolume.resource_type).resource_type_id,
                ResourceProperty.name == 'attachments',
                func.JSON_CONTAINS(ResourceProperty.value, func.JSON_QUOTE(self.id))
            ).all()
        ]
    # endregion

    @deprecated('`update` is deprecated, please use `update_resource` instead')
    def update(self, data):
        """Updates the object information based on live data, if there were any changes made. Any changes will be
        automatically applied to the object, but will not be automatically persisted. You must manually call
        `db.session.add(instance)` on the object.

        Args:
            data (:obj:): AWS API Resource object fetched from AWS API

        Returns:
            True if there were any changes to the object, else false
        """
        # If the instance was terminated, remove it
        if data.state['Name'] == 'terminated':
            self.delete(auto_commit=False)
            return True

        args = {
            'launch_date': to_utc_date(data.launch_time).isoformat(),
            'state': data.state['Name'],
            'instance_type': data.instance_type,
            'public_ip': data.public_ip_address or None,
            'public_dns': data.public_dns_name or None,
        }

        return self.update_resource(
            properties=args,
            tags={x['Key']: x['Value'] for x in data.tags or {}}
        )

    def get_name_or_instance_id(self, with_id=False):
        """Returns the name of an instance if existant, else return the instance id

        Args:
            with_id (bool): Include the instance ID even if the name is found (default: False)

        Returns:
            Name and/or instance ID of the instance object
        """
        super().get_name_or_id(with_id=with_id)

    @classmethod
    def search_by_age(cls, *, limit=100, page=1, accounts=None, locations=None, age=720,
                      properties=None, include_disabled=False):
        """Search for resources based on the provided filters

        Args:
            limit (`int`): Number of results to return. Default: 100
            page (`int`): Pagination offset for results. Default: 1
            accounts (`list` of `int`): A list of account id's to limit the returned resources to
            locations (`list` of `str`): A list of locations as strings to limit the search for
            age (`int`): Age of instances older than `age` days to return
            properties (`dict`): A `dict` containing property name and value pairs. Values can be either a str or a list
            of strings, in which case a boolean OR search is performed on the values
            include_disabled (`bool`): Include resources from disabled accounts. Default: False

        Returns:
            `list` of `Resource`
        """
        qry = cls.search(
            limit=limit,
            page=page,
            resource_types=[ResourceType.get(cls.resource_type).resource_type],
            accounts=accounts,
            locations=locations,
            properties=properties,
            include_disabled=include_disabled,
            return_query=True
        )

        age_alias = aliased(ResourceProperty)
        qry = (
            qry.join(age_alias, Resource.resource_id == age_alias.resource_id).filter(
                age_alias.name == 'launch_date',
                cast(func.JSON_UNQUOTE(age_alias.value), DATETIME) < datetime.now() - timedelta(days=age)
            )
        )

        total = qry.count()
        qry = qry.limit(limit)
        qry = qry.offset((page - 1) * limit if page > 1 else 0)

        return total, [cls(x) for x in qry.all()]


class BeanStalk(BaseResource):
    """Elastic Beanstalk object"""
    resource_type = 'aws_beanstalk'
    resource_name = 'Elastic BeanStalk'
    resource_properties = [
        ResourceProp(key='environment_name', name='Environment Name', type='string', show=True),
        ResourceProp(key='application_name', name='Application Name', type='string', show=True),
        ResourceProp(key='cname', name='CNAME', type='string', show=True)
    ]

    @deprecated('`update` is deprecated, please use `update_resource` instead')
    def update(self, data):
        return self.update_resource(
            properties={
                'environment_name': data['environment_name'],
                'application_name': data['application_name'],
                'cname': data['cname']
            }
        )


class CloudFrontDist(BaseResource):
    """CloudFront Distribution object"""
    resource_type = 'aws_cloudfront_dist'
    resource_name = 'CloudFront Distribution'
    resource_properties = [
        ResourceProp(key='arn', name='ARN', type='string', show=True),
        ResourceProp(key='domain_name', name='Domain Name', type='string', show=True),
        ResourceProp(key='origins', name='Origins', type='json', show=True),
        ResourceProp(key='enabled', name='Enabled', type='bool', show=True),
        ResourceProp(key='type', name='Type', type='string', show=True),
    ]

    @deprecated('`update` is deprecated, please use `update_resource` instead')
    def update(self, data):
        properties = {
            'domain_name': data['name'],
            'origins': data['origins'],
            'enabled': data['enabled'],
            'type': data['type']
        }
        tags = data.pop('tags')

        return self.update_resource(properties=properties, tags=tags)


class S3Bucket(BaseResource):
    """S3 Bucket object"""
    resource_type = 'aws_s3_bucket'
    resource_name = 'S3 Bucket'
    resource_properties = [
        ResourceProp(key='creation_date', name='Creation Date', type='datetime', show=True),
        ResourceProp(key='bucket_policy', name='Bucket Policy', type='json', show=True),
        ResourceProp(key='website_enabled', name='Website Enabled', type='bool', show=True),
        ResourceProp(key='metrics', name='Bucket Metrics', type='json', show=True),
    ]

    @property
    def resource_creation_date(self):
        return self.creation_date

    @deprecated('`update` is deprecated, please use `update_resource` instead')
    def update(self, data, properties):
        properties = {
            'location': properties['location'],
            'creation_date': data.creation_date,
            'bucket_policy': properties['bucket_policy'],
            'website_enabled': properties['website_enabled'],
            'metrics': properties['metrics']
        }

        try:
            tags = {t['Key']: t['Value'] for t in data.Tagging().tag_set}
        except ClientError:
            tags = None

        return self.update_resource(properties=properties, tags=tags)


class EBSSnapshot(BaseResource):
    """EBS Snapshot object"""
    resource_type = 'aws_ebs_snapshot'
    resource_name = 'EBS Snapshot'
    resource_properties = [
        ResourceProp(key='state', name='State', type='string', show=True),
        ResourceProp(key='state_message', name='State Message', type='string', show=True),
        ResourceProp(key='encrypted', name='Encrypted', type='string', show=True),
        ResourceProp(key='kms_key_id', name='KMS Key ID', type='string', show=True),
        ResourceProp(key='volume_id', name='Volume ID', type='string', show=True),
        ResourceProp(key='volume_size', name='Volume Size', type='string', show=True),
    ]

    @deprecated('`update` is deprecated, please use `update_resource` instead')
    def update(self, data):
        """Updates the object information based on live data, if there were any changes made. Any changes will be
        automatically applied to the object, but will not be automatically persisted. You must manually call
        `db.session.add(snapshot)` on the object.

        Args:
            data (bunch): Data fetched from AWS API

        Returns:
            True if there were any changes to the object, else false
        """

        return self.update_resource(
            properties={
                'state': data.state,
                'state_message': data.state_message
            },
            tags={x['Key']: x['Value'] for x in data.tags or {}}
        )


class EBSVolume(BaseResource):
    """EBS Volume object"""
    resource_type = 'aws_ebs_volume'
    resource_name = 'EBS Volume'

    resource_properties = [
        ResourceProp(key='create_time', name='Creation Time', type='datetime', show=True),
        ResourceProp(key='state', name='State', type='string', show=True),
        ResourceProp(key='iops', name='IOPS', type='string', show=True),
        ResourceProp(key='encrypted', name='Encrypted', type='bool', show=True),
        ResourceProp(key='kms_key_id', name='KMS Key ID', type='string', show=True),
        ResourceProp(key='snapshot_id', name='Snapshot ID', type='string', show=True),
        ResourceProp(key='size', name='Size', type='string', show=True),
        ResourceProp(key='attachments', name='Attachments', type='dict', show=True),
        ResourceProp(key='volume_type', name='Volume Type', type='string', show=True),
    ]

    @deprecated('`update` is deprecated, please use `update_resource` instead')
    def update(self, data):
        """Updates the object information based on live data, if there were any changes made. Any changes will be
        automatically applied to the object, but will not be automatically persisted. You must manually call
        `db.session.add(volume)` on the object.

        Args:
            data (bunch): Data fetched from AWS API

        Returns:
            True if there were any relevant changes to the object, else false
        """
        return self.update_resource(
            properties={
                'state': data.state,
                'attachments': sorted(attachment['InstanceId'] for attachment in data.attachments)
            },
            tags={x['Key']: x['Value'] for x in data.tags or {}}
        )

    def __str__(self):
        return '{}: {}GB @ {}'.format(self.id, self.size, self.state)


class AMI(BaseResource):
    """AMI object"""
    resource_type = 'aws_ami'
    resource_name = 'AMI'
    resource_properties = [
        ResourceProp(key='architecture', name='Architecture', type='string', show=True),
        ResourceProp(key='creation_date', name='Creation Date', type='datetime', show=True),
        ResourceProp(key='description', name='Description', type='string', show=True),
        ResourceProp(key='name', name='Name', type='string', show=True),
        ResourceProp(key='platform', name='Platform', type='string', show=True),
        ResourceProp(key='state', name='State', type='string', show=True)
    ]

    @deprecated('`update` is deprecated, please use `update_resource` instead')
    def update(self, data):
        """Updates the object information based on live data, if there were any changes made. Any changes will be
        automatically applied to the object, but will not be automatically persisted. You must manually call
        `db.session.add(ami)` on the object.

        Args:
            data (bunch): Data fetched from AWS API

        Returns:
            True if there were any changes to the object, else false
        """
        return self.update_resource(
            properties={
                'description': data.description,
                'state': data.state
            },
            tags={x['Key']: x['Value'] for x in data.tags or {}}
        )


class DNSZone(BaseResource):
    """DNS Zone object"""
    resource_type = 'dns_zone'
    resource_name = 'DNS Zone'
    resource_properties = [
        ResourceProp(key='name', name='Name', type='string', show=True),
        ResourceProp(key='source', name='Source', type='string', show=True),
        ResourceProp(key='private_zone', name='Private Zone', type='string', show=True),
        ResourceProp(key='comment', name='Comment', type='string', show=True),
    ]

    # region Object properties
    @property
    def records(self):
        return [DNSRecord(res) for res in self.children]
    # endregion

    # region Instance methods
    @deprecated('`add_record` is deprecated, please use `add_child`')
    def add_record(self, record):
        """Add

        Args:
            record (:obj:`DNSRecord`): :obj:`DNSRecord` to add

        Returns:
            `None`
        """
        self.add_child(record)

    @deprecated('`delete_record` is deprecated, please use `delete_child`')
    def delete_record(self, record):
        """Remove a DNSRecord

        Args:
            record (:obj:`DNSRecord`): :obj:`DNSRecord` to remove

        Returns:
            `None`
        """
        self.delete_child(record)

    @deprecated('`update` is deprecated, please use `update_resource` instead')
    def update(self, data):
        """Updates the object information based on live data, if there were any changes made. Any changes will be
        automatically applied to the object, but will not be automatically persisted. You must manually call
        `db.session.add(ami)` on the object.

        Args:
            data (bunch): Data fetched from AWS API

        Returns:
            True if there were any changes to the object, else false
        """
        return self.update_resource(
            properties={
                'comment': data['comment']
            },
            tags=data['tags']
        )

    def to_json(self, with_records=True):
        data = super().to_json()
        if with_records:
            data['recordCount'] = len(self.records)
            data['records'] = self.records

        return data
    # endregion


class DNSRecord(BaseResource):
    """DNS Record object"""
    resource_type = 'dns_record'
    resource_name = 'DNS Record'
    resource_properties = [
        ResourceProp(key='name', name='Name', type='string', show=True),
        ResourceProp(key='type', name='Type', type='string', show=True),
        ResourceProp(key='ttl', name='TTL', type='string', show=True),
        ResourceProp(key='value', name='Value', type='string', show=True),
    ]

    # region Object properties
    @property
    @deprecated('`zone` is deprecated, please use `parents`')
    def zone(self):
        """Returns the DNSZone that the record is hosted in

        Returns:
            :obj:`DNSZone`
        """
        return DNSZone(self.parents[0])

    # endregion

    @deprecated('`update` is deprecated, please use `update_resource` instead')
    def update(self, data):
        return self.update_resource(properties={'value': data['value']})


class VPC(BaseResource):
    """VPC Object"""
    resource_type = 'aws_vpc'
    resource_name = 'VPC'
    resource_properties = [
        ResourceProp(key='cidr_v4', name='IPv4 CIDR', type='string', show=True),
        ResourceProp(key='is_default', name='Default VPC', type='bool', show=True),
        ResourceProp(key='state', name='STate', type='string', show=True),
        ResourceProp(key='vpc_flow_logs_status', name='VPC Flow Log Status', type='string', show=True),
        ResourceProp(key='vpc_flow_logs_log_group', name='VPC Flow Log Group', type='string', show=True),
    ]

    @deprecated('`update` is deprecated, please use `update_resource` instead')
    def update(self, data, properties):
        """Updates the object information based on live data, if there were any changes made. Any changes will be
        automatically applied to the object, but will not be automatically persisted. You must manually call
        `db.session.add(vpc)` on the object.

        Args:
            data (bunch): Data fetched from AWS API
            properties (bunch): Properties of the VPC and CloudWatch Log Group as fetched from AWS API

        Returns:
            True if there were any changes to the object, else false
        """
        properties = {
            'cidr_v4': data.cidr_block,
            'is_default': data.is_default,
            'state': data.state,
            'vpc_flow_logs_status': properties['vpc_flow_logs_status'],
            'vpc_flow_logs_group': properties['vpc_flow_logs_log_group']
        }

        return self.update_resource(
            properties=properties,
            tags={x['Key']: x['Value'] for x in data.tags or {}}
        )
