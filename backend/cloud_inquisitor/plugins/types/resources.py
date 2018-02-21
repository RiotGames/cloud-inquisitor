import logging
import re
from abc import abstractmethod, ABC
from contextlib import suppress
from datetime import datetime, timedelta

from botocore.exceptions import ClientError
from dateutil import parser
from flask import session
from sqlalchemy import func, or_, and_, cast, DATETIME
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased

from cloud_inquisitor.constants import RGX_EMAIL_VALIDATION_PATTERN
from cloud_inquisitor.database import db
from cloud_inquisitor.exceptions import ResourceException
from cloud_inquisitor.schema import Tag, Account, Resource, ResourceType, ResourceProperty
from cloud_inquisitor.utils import to_utc_date, is_truthy, to_camelcase


class BaseResource(ABC):
    """Base type object for resource objects"""
    def __init__(self, resource):
        self.resource = resource
        self.log = logging.getLogger(self.__class__.__module__)

    def __getattr__(self, item):
        return self.get_property(item)

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

    @abstractmethod
    def update(self, data):
        """Updates the resource object with the information from `data`. The changes will be added to the current
        db.session but will not be commited. The user will need to perform the commit explicitly to save the changes

        Returns:
            True if resource object was updated, else False
        """

    # region Class methods
    @classmethod
    def get(cls, resource_id):
        """Returns the class object identified by `resource_id`

        Args:
            resource_id (str): Unique EC2 Instance ID to load from database

        Returns:
            EC2 Instance object if found, else None
        """
        res = Resource.get(resource_id)
        return cls(res) if res else None

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
    def search(cls, *, limit=100, page=1, accounts=None, locations=None,
               properties=None, include_disabled=False, return_query=False):
        """Search for resources based on the provided filters. If `return_query` a sub-class of `sqlalchemy.orm.Query`
        is returned instead of the resource list.

        Args:
            limit (`int`): Number of results to return. Default: 100
            page (`int`): Pagination offset for results. Default: 1
            accounts (`list` of `int`): A list of account id's to limit the returned resources to
            locations (`list` of `str`): A list of locations as strings to limit the search for
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
    # endregion

    # region Instance methods
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

    def set_property(self, name, value, update_session=True):
        """Create or set the value of a property. Returns `True` if the property was created or updated, or `False` if
        there were no changes to the value of the property.

        Args:
            name (str): Name of the property to create or update
            value (any): Value of the property. This can be any type of JSON serializable data
            update_session (bool): Automatically add the change to the SQLAlchemy session. Default: True

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

        if update_session:
            db.session.add(prop)

        return True

    def delete_property(self, name, update_session=True):
        """Removes a property from an object, by the name of the property. Returns `True` if the property was removed or
        `False` if the property didn't exist.

        Args:
            name (str): Name of the property to delete
            update_session (bool): Automatically add the change to the SQLAlchemy session. Default: True

        Returns:
            `bool`
        """
        try:
            self.log.debug('Removing property {} from {}'.format(name, self.id))
            prop = getattr(self, name)
            self.properties.remove(prop)

            if update_session:
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

    def to_json(self):
        """Return a `dict` representation of the resource, including all properties and tags

        Returns:
            `dict`
        """
        return {
            'resourceType': self.resource.resource_type_id,
            'resourceId': self.id,
            'accountId': self.resource.account_id,
            'account': self.account,
            'location': self.resource.location,
            'properties': {to_camelcase(prop.name): prop.value for prop in self.resource.properties},
            'tags': [{'key': t.key, 'value': t.value} for t in self.resource.tags]
        }
    # endregion


class EC2Instance(BaseResource):
    """EC2 Instance"""
    resource_type = 'aws_ec2_instance'
    resource_name = 'EC2 Instance'

    # region Object properties
    @property
    def launch_date(self):
        """Returns the time and date of the last time the instance was started

        Returns:
            `datetime`
        """
        return parser.parse(self.get_property('launch_date').value)

    @property
    def state(self):
        """Returns the current state of the instance, eg. `running`, `stopped` etc.

        Returns:
            `str`
        """
        return self.get_property('state').value

    @property
    def instance_type(self):
        """Returns the instance type, eg. `m4.large`, `r3.xlarge`

        Returns:
            `str`
        """
        return self.get_property('instance_type').value

    @property
    def public_ip(self):
        """Returns the publicly accessible IP address. `None` if instance does not have a public address

        Returns:
            `str`
        """
        return self.get_property('public_ip').value

    @property
    def public_dns(self):
        """Returns the publicly accessible DNS name. `None` if instance does not have a public address

        Returns:
            `str`
        """
        return self.get_property('public_dns').value

    @property
    def created(self):
        """Returns the date and time for when this instance was first discovered

        Returns:
            `str`
        """
        return self.get_property('created').value

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
                Resource.resource_type_id == ResourceType.get('aws_ebs_volume').resource_type_id,
                ResourceProperty.name == 'attachments',
                func.JSON_CONTAINS(ResourceProperty.value, func.JSON_QUOTE(self.id))
            ).all()
        ]
    # endregion

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

        updated = self.set_property('launch_date', to_utc_date(data.launch_time).isoformat())
        updated |= self.set_property('state', data.state['Name'])
        updated |= self.set_property('instance_type', data.instance_type)
        updated |= self.set_property('public_ip', data.public_ip_address or None)
        updated |= self.set_property('public_dns', data.public_dns_name or None)

        tags = {x['Key']: x['Value'] for x in data.tags or {}}
        existing_tags = {x.key: x for x in self.tags}

        # Check for new tags
        for key, value in list(tags.items()):
            updated |= self.set_tag(key, value)

        # Check for updated or removed tags
        for key in list(existing_tags.keys()):
            if key not in tags:
                updated |= self.delete_tag(key)

        return updated

    def get_name_or_instance_id(self, with_id=False):
        """Returns the name of an instance if existant, else return the instance id

        Args:
            with_id (bool): Include the instance ID even if the name is found (default: False)

        Returns:
            Name and/or instance ID of the instance object
        """
        name = self.get_tag('Name', case_sensitive=False)
        if name and len(name.value.strip()) > 0:
            return '{0} ({1})'.format(name.value, self.id) if with_id else name.value

        return self.id

    def get_owner_emails(self, partial_owner_match=True):
        """Return a list of email addresses associated with the instance, based on tags

        Returns:
            List of email addresses if any, else None
        """
        for tag in self.tags:
            if tag.key.lower() == 'owner':
                rgx = re.compile(RGX_EMAIL_VALIDATION_PATTERN, re.I)
                if partial_owner_match:
                    m = rgx.findall(tag.value)
                    if m:
                        return m
                else:
                    m = rgx.match(tag.value)
                    if m:
                        return m.groups()

        return None

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
            accounts=accounts,
            locations=locations,
            properties=properties,
            include_disabled=include_disabled,
            return_query=True
        )

        age_alias = aliased(ResourceProperty)
        qry = (
            qry.join(age_alias, Resource.resource_id == age_alias.resource_id)
            .filter(
                age_alias.name == 'launch_date',
                cast(func.JSON_UNQUOTE(age_alias.value), DATETIME) < datetime.now() - timedelta(days=age)
            )
        )

        total = qry.count()
        qry = qry.limit(limit)
        qry = qry.offset((page - 1) * limit if page > 1 else 0)

        return total, [cls(x) for x in qry.all()]

    def to_json(self, with_volumes=True):
        """Augment the base `to_json` function, adding information about volumes

        Returns:
            `dict`
        """
        data = super().to_json()
        if with_volumes:
            data['volumes'] = [
                {
                    'volumeId': vol.id,
                    'volumeType': vol.volume_type,
                    'size': vol.size
                } for vol in self.volumes
            ]

        return data


class BeanStalk(BaseResource):
    """Elastic Beanstalk object"""
    resource_type = 'aws_beanstalk'
    resource_name = 'Elastic BeanStalk'

    # region Object properties
    @property
    def environment_name(self):
        """Returns the Elastic BeanStalk environment name"""
        return self.get_property('environment_name').value

    @property
    def application_name(self):
        """Returns the application name of the Elastic BeanStalk"""
        return self.get_property('application_name').value

    @property
    def cname(self):
        """Returns the DNS CNAME of the Elastic BeanStalk"""
        return self.get_property('cname').value
    # endregion

    def update(self, data):
        updated = self.set_property('environment_name', data['environment_name'])
        updated |= self.set_property('application_name', data['application_name'])
        updated |= self.set_property('cname', data['cname'])

        return updated


class CloudFrontDist(BaseResource):
    """CloudFront Distribution object"""
    resource_type = 'aws_cloudfront_dist'
    resource_name = 'CloudFront Distribution'

    # region Object properties
    @property
    def domain_name(self):
        """Returns the domain name of the CloudFront distribution

        Returns:
            `str`
        """
        return self.get_property('domain_name').value

    @property
    def origins(self):
        """Returns the list of origins for the distribution

        Returns:
            `list` of `str`
        """
        return self.get_property('origins').value

    @property
    def enabled(self):
        """Return `True` if the distribution is enabled, else `False`

        Returns:
            `bool`
        """
        return is_truthy(self.get_property('enabled').value)

    @property
    def type(self):
        """Returns the type of distribution. Currently supported: `web` and `rtmp`

        Returns:
            `str`
        """
        return self.get_property('type').value
    # endregion

    def update(self, data):
        tags = data.pop('tags')
        existing_tags = {x.key: x for x in self.tags}

        updated = self.set_property('domain_name', data['name'])
        updated |= self.set_property('origins', data['origins'])
        updated |= self.set_property('enabled', data['enabled'])
        updated |= self.set_property('type', data['type'])

        # Check for new tags
        for key, value in list(tags.items()):
            updated |= self.set_tag(key, value)

        # Check for updated or removed tags
        for key in list(existing_tags.keys()):
            if key not in tags:
                updated |= self.delete_tag(key)

        return updated


class S3Bucket(BaseResource):
    """S3 Bucket object"""
    resource_type = 'aws_s3_bucket'
    resource_name = 'S3 Bucket'

    # region Object properties
    @property
    def creation_date(self):
        """Returns the date and time the bucket was created.

        Returns:
            `str`
        """
        return self.get_property('creation_date').value
    # endregion

    def update(self, data):
        updated = False

        with suppress(ClientError):
            tags = {t['Key']: t['Value'] for t in data.Tagging().tag_set}
            existing_tags = {x.key: x for x in self.tags}

            # Check for new tags
            for key, value in list(tags.items()):
                updated |= self.set_tag(key, value)

            # Check for updated or removed tags
            for key in list(existing_tags.keys()):
                if key not in tags:
                    updated |= self.delete_tag(key)

        return updated


class EBSSnapshot(BaseResource):
    """EBS Snapshot object"""
    resource_type = 'aws_ebs_snapshot'
    resource_name = 'EBS Snapshot'

    # region Object properties
    @property
    def state(self):
        """Returns the current state of the snapshot

        Returns:
            `str`
        """
        return self.get_property('state').value

    @property
    def state_message(self):
        """Returns information about the current state

        Returns:
            `str`
        """
        return self.get_property('state_message').value

    @property
    def encrypted(self):
        """Returns `True` if the snapshot is encrypted with KMS, else `False`

        Returns:
            `bool`
        """
        return is_truthy(self.get_property('encrypted').value)

    @property
    def kms_key_id(self):
        """Returns the ARN of the KMS key used to encrypt the snapshot (if applicable, else `None`)

        Returns:
            `str`
        """
        return self.get_property('kms_key_id').value

    @property
    def volume_id(self):
        """Returns the ID of the volume used to create the snapshot

        Returns:
            `str`
        """
        return self.get_property('volume_id').value

    @property
    def volume_size(self):
        """Returns the size of the original volume used to create the snapshot.

        *NOTE*
        Snapshots are stored compressed, so the `volume_size` does not reflect the true size of the snapshot itself.

        Returns:
            `str`
        """
        return self.get_property('volume_size').value
    # endregion

    def update(self, data):
        """Updates the object information based on live data, if there were any changes made. Any changes will be
        automatically applied to the object, but will not be automatically persisted. You must manually call
        `db.session.add(snapshot)` on the object.

        Args:
            data (bunch): Data fetched from AWS API

        Returns:
            True if there were any changes to the object, else false
        """
        updated = self.set_property('state', data.state)
        updated |= self.set_property('state_message', data.state_message)

        tags = {x['Key']: x['Value'] for x in data.tags or {}}
        existing_tags = {x.key: x for x in self.tags}

        # Check for new tags
        for key, value in list(tags.items()):
            updated |= self.set_tag(key, value)

        # Check for updated or removed tags
        for key in list(existing_tags.keys()):
            if key not in tags:
                updated |= self.delete_tag(key)

        return updated


class EBSVolume(BaseResource):
    """EBS Volume object"""
    resource_type = 'aws_ebs_volume'
    resource_name = 'EBS Volume'

    # region Object properties
    @property
    def create_time(self):
        """Returns the date and time of volume creation

        Returns:
            `str`
        """
        return self.get_property('create_time').value

    @property
    def state(self):
        """Returns the current state of the snapshot

        Returns:
            `str`
        """
        return self.get_property('state').value

    @property
    def iops(self):
        """Returns the provisioned IOPS (if applicable)

        Returns:
            `str`
        """
        return self.get_property('iops').value

    @property
    def encrypted(self):
        """Returns `True` if the snapshot is encrypted with KMS, else `False`

        Returns:
            `bool`
        """
        return is_truthy(self.get_property('encrypted').value)

    @property
    def kms_key_id(self):
        """Returns the ARN of the KMS key used to encrypt the snapshot (if applicable, else `None`)

        Returns:
            `str`
        """
        return self.get_property('kms_key_id').value

    @property
    def snapshot_id(self):
        """Returns the ID of the snapshot used to create the volume (if applicable)

        Returns:
            `str`
        """
        return self.get_property('snapshot_id').value

    @property
    def size(self):
        """Returns the size of the volume

        Returns:
            `str`
        """
        return self.get_property('size').value

    @property
    def attachments(self):
        """Returns a list of the IDs of the instances the volume is attached to

        Returns:
            `list` of `str`
        """
        return self.get_property('attachments').value

    @property
    def volume_type(self):
        """Returns the type of volume, eg. `gp2` or `io1`

        Returns:
            `str`
        """
        return self.get_property('volume_type').value
    # endregion

    def update(self, data):
        """Updates the object information based on live data, if there were any changes made. Any changes will be
        automatically applied to the object, but will not be automatically persisted. You must manually call
        `db.session.add(volume)` on the object.

        Args:
            data (bunch): Data fetched from AWS API

        Returns:
            True if there were any relevant changes to the object, else false
        """
        updated = self.set_property('state', data.state)
        updated |= self.set_property('attachments', sorted(attachment['InstanceId'] for attachment in data.attachments))

        tags = {x['Key']: x['Value'] for x in data.tags or {}}
        existing_tags = {x.key: x for x in self.tags}

        # Check for new tags
        for key, value in list(tags.items()):
            updated |= self.set_tag(key, value)

        # Check for updated or removed tags
        for key in list(existing_tags.keys()):
            if key not in tags:
                updated |= self.delete_tag(key)

        return updated

    def __str__(self):
        return '{}: {}GB @ {}'.format(self.id, self.size, self.state)


class AMI(BaseResource):
    """AMI object"""
    resource_type = 'aws_ami'
    resource_name = 'AMI'

    # region Object properties
    @property
    def architecture(self):
        """Returns the architecture of the AMI, eg. `x86_64`

        Returns:
            `str`
        """
        return self.get_property('architecture').value

    @property
    def creation_date(self):
        """Returns the date and time the image was created

        Returns:
            `str`
        """
        return self.get_property('creation_date').value

    @property
    def description(self):
        """Returns the description of the AMI

        Returns:
            `str`
        """
        return self.get_property('description').value

    @property
    def name(self):
        """Returns the name of the image

        Returns:
            `str`
        """
        return self.get_property('name').value

    @property
    def platform(self):
        """Returns the platform of the image, eg. `Linux` or `Windows`

        Returns:
            `str`
        """
        return self.get_property('platform').value

    @property
    def state(self):
        """Returns the state of the image, eg `available` or `pending`

        Returns:
            `str`
        """
        return self.get_property('state').value
    # endregion

    def update(self, data):
        """Updates the object information based on live data, if there were any changes made. Any changes will be
        automatically applied to the object, but will not be automatically persisted. You must manually call
        `db.session.add(ami)` on the object.

        Args:
            data (bunch): Data fetched from AWS API

        Returns:
            True if there were any changes to the object, else false
        """
        updated = self.set_property('description', data.description)
        updated |= self.set_property('state', data.state)

        tags = {x['Key']: x['Value'] for x in data.tags or {}}
        existing_tags = {x.key: x for x in self.tags}

        # Check for new tags
        for key, value in list(tags.items()):
            updated |= self.set_tag(key, value)

        # Check for updated or removed tags
        for key in list(existing_tags.keys()):
            if key not in tags:
                updated |= self.delete_tag(key)

        return updated


class DNSZone(BaseResource):
    """DNS Zone object"""
    resource_type = 'dns_zone'
    resource_name = 'DNS Zone'

    # region Object properties
    @property
    def name(self):
        """Returns the FQDN of the zone

        Returns:
            `str`
        """
        return self.get_property('domain_name').value

    @property
    def source(self):
        """Returns the source of the DNS zone, ex: `AWS/<account_name>` or `CloudFlare`

        Returns:
            `str`
        """
        return self.get_property('source').value

    @property
    def private_zone(self):
        """Returns `True` if the zone is only available internally (no Internet access), else `False`

        Returns:
            `bool`
        """
        return is_truthy(self.get_property('private_zone').value)

    @property
    def comment(self):
        """Returns the comment for the hosted zone

        Returns:
            `str`
        """
        return self.get_property('comment').value

    @property
    def records(self):
        return [DNSRecord(res) for res in self.children]
    # endregion

    # region Instance methods
    def add_record(self, record):
        """Add

        Args:
            record (:obj:`DNSRecord`): :obj:`DNSRecord` to add

        Returns:
            `None`
        """
        self.children.append(record.resource)

    def delete_record(self, record):
        """Remove a DNSRecord

        Args:
            record (:obj:`DNSRecord`): :obj:`DNSRecord` to remove

        Returns:
            `None`
        """
        self.children.remove(record.resource)
        record.delete()

    def update(self, data):
        """Updates the object information based on live data, if there were any changes made. Any changes will be
        automatically applied to the object, but will not be automatically persisted. You must manually call
        `db.session.add(ami)` on the object.

        Args:
            data (bunch): Data fetched from AWS API

        Returns:
            True if there were any changes to the object, else false
        """
        updated = self.set_property('comment', data['comment'])

        tags = data['tags']
        existing_tags = {x.key: x for x in self.tags}
        # Check for new tags
        for key, value in list(tags.items()):
            updated |= self.set_tag(key, value)

        # Check for updated or removed tags
        for key in list(existing_tags.keys()):
            if key not in tags:
                updated |= self.delete_tag(key)

        return updated

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

    # region Object properties
    @property
    def name(self):
        """Returns the name of the resource record

        Returns:
            `str`
        """
        return self.get_property('name').value

    @property
    def type(self):
        """Returns the resource record type, eg. `A`, `CNAME` and `MX`

        Returns:
            `str`
        """
        return self.get_property('type').value

    @property
    def ttl(self):
        """Returns the resource record Time-To-Live (TTL)

        Returns:
            `str`
        """
        return self.get_property('ttl').value

    @property
    def value(self):
        """Returns the value of the resource record set, as a list of targets

        Returns:
            `list` of `str`
        """
        return self.get_property('value').value

    @property
    def zone(self):
        """Returns the DNSZone that the record is hosted in

        Returns:
            :obj:`DNSZone`
        """
        return DNSZone(self.parents[0])
    # endregion

    def update(self, data):
        updated = self.set_property('value', data['value'])

        return updated


class VPC(BaseResource):
    """VPC Object"""
    resource_type = 'aws_vpc'
    resource_name = 'VPC'

    # region Object properties
    @property
    def cidr_v4(self):
        """ Returns the IPv4 CIDR block associated with the VPC

        Returns:
            `str`

        """
        return self.get_property('cidr_v4').value

    @property
    def state(self):
        """ Returns the current state of the VPC (pending/available)

        Returns:
            `str`

        """
        return self.get_property('state').value

    @property
    def vpc_flow_logs_status(self):
        """ Returns the configured state of VPC Flow Logs

        Returns:
            `str`

        """
        return self.get_property('vpc_flow_logs_status').value

    def vpc_flow_logs_log_group(self):
        """ Returns the CloudWatch Log Group associated with the VPC Flow Logs

        Returns:
            `str`

        """
        return self.get_property('vpc_flow_logs_log_stream').value

    # end of region

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

        updated = self.set_property('cidr_v4', data.cidr_block)
        updated |= self.set_property('state', data.state)
        updated |= self.set_property('vpc_flow_logs_status', properties['vpc_flow_logs_status'])
        updated |= self.set_property('vpc_flow_logs_log_stream', properties['vpc_flow_logs_log_group'])

        tags = {x['Key']: x['Value'] for x in data.tags or {}}
        existing_tags = {x.key: x for x in self.tags}

        # Check for new tags
        for key, value in list(tags.items()):
            updated |= self.set_tag(key, value)

        # Check for updated or removed tags
        for key in list(existing_tags.keys()):
            if key not in tags:
                updated |= self.delete_tag(key)

        return updated
