import logging
from abc import abstractmethod, ABC
from collections import namedtuple
from datetime import datetime

from sqlalchemy import or_, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased

from cloud_inquisitor import get_plugin_by_name, PLUGIN_NAMESPACES
from cloud_inquisitor.database import db
from cloud_inquisitor.exceptions import IssueException, InquisitorError
from cloud_inquisitor.plugins.types.resources import Resource, EBSVolume
from cloud_inquisitor.schema import IssueProperty, Issue, IssueType
from cloud_inquisitor.utils import to_camelcase, parse_date, is_truthy, deprecated

IssueProp = namedtuple('IssueProp', ('key', 'name', 'type', 'show', 'primary'))


class BaseIssue(ABC):
    issue_properties = []

    """Base type object for issue objects"""
    def __init__(self, issue):
        self.issue = issue
        self.log = logging.getLogger(self.__class__.__module__)

    def __getattr__(self, item):
        for prop in self.issue_properties:
            if prop.key == item:
                if prop.type == 'datetime':
                    return parse_date(self.get_property(item).value)

                elif prop.type == 'bool':
                    return is_truthy(self.get_property(item).value)

                return self.get_property(item).value

        raise AttributeError('{} has no attribute {}'.format(self.__class__.__name__, item))

    def __str__(self):
        return '<{} issue_id={}>'.format(self.__class__.__name__, self.id)

    # region Static and Class methods
    @abstractmethod
    def update(self, data):
        """Updates the issue object with the information from `data`. The changes will be added to the current
        db.session but will not be commited. The user will need to perform the commit explicitly to save the changes

        Returns:
            True if issue object was updated, else False
        """

    @staticmethod
    def get(issue_id):
        """Returns the class object identified by `issue_id`

        Args:
            issue_id (str): Unique issue ID

        Returns:
            Issue object if found, else None
        """
        issue = Issue.get(issue_id)

        if not issue:
            return None

        issue_type = IssueType.get(issue.issue_type_id).issue_type
        issue_class = get_plugin_by_name(PLUGIN_NAMESPACES['issues'], issue_type)

        return issue_class(issue)

    @classmethod
    def create(cls, issue_id, *, properties=None, auto_add=True, auto_commit=False):
        """Creates a new Resource object with the properties and tags provided

        Args:
            issue_id (str): Unique identifier for the resource object
            properties (dict): Dictionary of properties for the resource object.
            auto_add (bool): Automatically add the new resource to the DB session. Default: True
            auto_commit (bool): Automatically commit the change to the database. Default: False
        """
        if cls.get(issue_id):
            raise IssueException('Issue {} already exists'.format(issue_id))

        issue = Issue()
        issue.issue_id = issue_id
        issue.issue_type_id = IssueType.get(cls.issue_type).issue_type_id

        if properties:
            for name, value in properties.items():
                prop = IssueProperty()
                prop.issue_id = issue.issue_id
                prop.name = name
                prop.value = value.isoformat() if type(value) == datetime else value
                issue.properties.append(prop)
                db.session.add(prop)

        if auto_add:
            db.session.add(issue)

            if auto_commit:
                db.session.commit()

            return cls.get(issue.issue_id)
        else:
            return cls(issue)

    @classmethod
    def get_all(cls):
        """Returns a list of all resources for a given account, location and resource type.

        Returns:
            `list` - list of issue objects
        """
        if cls == BaseIssue:
            raise InquisitorError('get_all on BaseIssue is not supported')

        qry = db.Issue.filter(
            Issue.issue_type_id == IssueType.get(cls.issue_type).issue_type_id
        )

        return {res.issue_id: cls(res) for res in qry.all()}

    @staticmethod
    def get_typed_issue(issue):
        """Returns a given issue object as the proper type

        Args:
             issue (BaseIssue, str, int): An issue object

        Returns:
            `issue`
        """
        if type(issue) in (int, str):
            issue = Issue.get(issue)

        elif issubclass(issue.__class__, BaseIssue):
            issue = issue.issue

        issue_type = IssueType.get(issue.issue_type_id).issue_type
        issue_class = get_plugin_by_name(PLUGIN_NAMESPACES['issues'], issue_type)
        if not issue_class:
            raise InquisitorError('Unknown issue type: {}'.format(issue_type))

        return issue_class(issue)

    @classmethod
    @deprecated('The `search` method is deprecated, please use the `find` function instead')
    def search(cls, *, limit=100, page=1, properties=None, return_query=False):
        """Search for issues based on the provided filters

        Args:
            limit (`int`): Number of results to return. Default: 100
            page (`int`): Pagination offset for results. Default: 1
            properties (`dict`): A `dict` containing property name and value pairs. Values can be either a str or a list
            of strings, in which case a boolean OR search is performed on the values
            return_query (`bool`): Returns the query object prior to adding the limit and offset functions. Allows for
            sub-classes to amend the search feature with extra conditions. The calling function must handle pagination
            on its own

        Returns:
            `list` of `Issue`, `sqlalchemy.orm.Query`
        """
        qry = db.Issue.order_by(Issue.issue_id).filter(
            Issue.issue_type_id == IssueType.get(cls.issue_type).issue_type_id
        )

        if properties:
            for prop_name, value in properties.items():
                alias = aliased(IssueProperty)
                qry = qry.join(alias, Issue.issue_id == alias.issue_id)
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
    def find(cls, *, limit=25, page=0, issue_types=None, properties=None, return_query=False):
        """Search for issues based on the provided filters

        Args:
            limit (`int`): Number of results to return. Default: 25
            page (`int`): Pagination offset for results. Default: 0
            issue_types (`list` of `str`): List of Issue types to return
            properties (`dict`): A `dict` containing property name and value pairs. Values can be either a str or a list
            of strings, in which case a boolean OR search is performed on the values
            return_query (`bool`): Returns the query object prior to adding the limit and offset functions. Allows for
            sub-classes to amend the search feature with extra conditions. The calling function must handle pagination
            on its own

        Returns:
            `list` of `Issue`, `sqlalchemy.orm.Query`
        """
        qry = db.Issue.order_by(Issue.issue_type_id, Issue.issue_id)

        if cls != BaseIssue or issue_types:
            qry = qry.join(IssueType, Issue.issue_type_id == IssueType.issue_type_id).filter(
                IssueType.issue_type.in_(issue_types or [cls.issue_type])
            )

        if properties:
            for prop_name, value in properties.items():
                alias = aliased(IssueProperty)
                qry = qry.join(alias, Issue.issue_id == alias.issue_id)
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

        return total, list(map(BaseIssue.get_typed_issue, qry.all()))
    # endregion

    # region Instance methods
    def update_issue(self, properties):
        """Updates the issue object

        The changes will be added to the current db.session but will not be commited. The user will need to perform the
        commit explicitly to save the changes

        Args:
            properties (`dict`): A dictionary of properties to update

        Returns:
            True if resource object was updated, else False
        """
        updated = False

        for prop in self.issue_properties:
            key = prop.key
            if key in properties:
                updated |= self.set_property(key, properties[key])

        return updated

    def get_property(self, item):
        """Return a named property for an issue, if available. Will raise an `AttributeError` if the property
        does not exist

        Args:
            item (str): Name of the property to return

        Returns:
            `IssueProperty`
        """
        for prop in self.issue.properties:
            if prop.name == item:
                return prop

        raise AttributeError(item)

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
            prop = IssueProperty()
            prop.issue_id = self.id
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
            db.session.add(self.issue)
            if auto_commit:
                db.session.commit()
        except SQLAlchemyError as ex:
            self.log.exception('Failed updating issue: {}'.format(ex))
            db.session.rollback()

    def delete(self, *, auto_commit=True):
        try:
            db.session.delete(self.issue)
            if auto_commit:
                db.session.commit()
        except SQLAlchemyError:
            self.log.exception('Failed deleting issue: {}'.format(self.id))
            db.session.rollback()

    def to_json(self):
        return {
            'issueType': self.issue.issue_type_id,
            'issueId': self.id,
            'properties': {to_camelcase(prop.name): prop.value for prop in self.issue.properties}
        }
    # endregion

    # region Object properties
    @property
    def id(self):
        return self.issue.issue_id

    @property
    def properties(self):
        return self.issue.properties

    @property
    @abstractmethod
    def issue_type(self):
        """The IssueType of the object"""

    @property
    @abstractmethod
    def issue_name(self):
        """Human friendly name of the issue type"""
    # endregion


class RequiredTagsIssue(BaseIssue):
    """Issue type for instances missing required tags"""
    issue_type = 'aws_required_tags'
    issue_name = 'Required Tags Issue'
    issue_properties = [
        IssueProp(key='resource_id', name='Resource ID', type='string', show=True, primary=False),
        IssueProp(key='created', name='Creation Time', type='timestamp', show=True, primary=False),
        IssueProp(key='account_id', name='Account ID', type='int', show=True, primary=False),
        IssueProp(key='location', name='Location', type='string', show=True, primary=False),
        IssueProp(key='state', name='State', type='int', show=True, primary=False),
        IssueProp(key='last_change', name='Last Change', type='datetime', show=True, primary=False),
        IssueProp(key='shutdown_on', name='Shutdown on', type='datetime', show=True, primary=False),
        IssueProp(key='missing_tags', name='Missing Tags', type='array', show=True, primary=True),
        IssueProp(key='notes', name='Notes', type='array', show=True, primary=False),
        IssueProp(key='last_alert', name='Last Alert', type='string', show=True, primary=False),
        IssueProp(key='resource_type', name='Resource Type', type='int', show=True, primary=False),
    ]

    # region Object properties
    @property
    def resource(self):
        """Return the instance object for the issue

        Returns:
            `Resource`
        """
        return Resource.get(self.resource_id)
    # endregion

    @deprecated('`update` is deprecated, please use `update_issue` instead')
    def update(self, data):
        """Updates the object information based on live data, if there were any changes made. Any changes will be
        automatically applied to the object, but will not be automatically persisted. You must manually call
        `db.session.add(instance)` on the object.

        Args:
            data (:obj:): AWS API Resource object fetched from AWS API

        Returns:
            `bool`
        """
        updated = False
        if 'missing_tags' in data:
            updated |= self.set_property('missing_tags', data['missing_tags'])

        if 'notes' in data:
            updated |= self.set_property('notes', data['notes'])

        if 'state' in data:
            updated |= self.set_property('state', data['state'])

        if 'last_alert' in data:
            updated |= self.set_property('last_alert', data['last_alert'])

        if updated:
            now = datetime.now()
            self.set_property('last_change', now)

        return updated

    def state_name(self):
        """Get a human-readable value of the state

        Returns:
            str: Name of the current state
        """
        if self.state == 1:
            return 'New Issue'

        elif self.state == 2:
            return 'Shutdown in 1 week'

        elif self.state == 3:
            return 'Shutdown in 1 day'

        elif self.state == 4:
            return 'Pending Shutdown'

        elif self.state == 5:
            return 'Stopped, delete in 12 weeks'

        elif self.state == 6:
            return 'Instance deleted'

        else:
            raise ValueError('Invalid state: {}'.format(self.state))

    def to_json(self):
        data = super().to_json()
        data['resource'] = self.resource

        return data


class DomainHijackIssue(BaseIssue):
    """Domain Hijacking Issue"""
    issue_type = 'domain_hijacking'
    issue_name = 'Domain Hijacking Issue'
    issue_properties = [
        IssueProp(key='issue_hash', name='Issue Hash', type='string', show=False, primary=False),
        IssueProp(key='source', name='Source', type='string', show=True, primary=False),
        IssueProp(key='description', name='Description', type='string', show=True, primary=True),
        IssueProp(key='state', name='State', type='string', show=True, primary=False),
        IssueProp(key='start', name='Start Time', type='datetime', show=True, primary=False),
        IssueProp(key='end', name='End', type='datetime', show=True, primary=False),
        IssueProp(key='last_alert', name='Last Alert', type='datetime', show=True, primary=False),
    ]

    @deprecated('`update` is deprecated, please use `update_issue` instead')
    def update(self, data):
        """Updates the object information based on live data, if there were any changes made. Any changes will be
        automatically applied to the object, but will not be automatically persisted. You must manually call
        `db.session.add(instance)` on the object.

        Args:
            data (:obj:): AWS API Resource object fetched from AWS API

        Returns:
            `bool`
        """
        # If the instance was terminated, remove it
        updated = False

        if 'state' in data:
            updated = self.set_property('state', data['state'])

        if 'end' in data:
            updated |= self.set_property('end', data['end'])

        if 'last_alert' in data:
            updated |= self.set_property('last_alert', data['last_alert'])

        return updated


class EBSVolumeAuditIssue(BaseIssue):
    """EBSVolume audit issue"""
    issue_type = 'aws_ebs_volume_audit'
    issue_name = 'EBS Volume Audit Issue'
    issue_properties = [
        IssueProp(key='volume_id', name='Volume ID', type='string', show=True, primary=False),
        IssueProp(key='account_id', name='Account ID', type='int', show=True, primary=False),
        IssueProp(key='location', name='Location', type='string', show=True, primary=False),
        IssueProp(key='state', name='State', type='string', show=True, primary=False),
        IssueProp(key='last_change', name='Last Change', type='datetime', show=True, primary=True),
        IssueProp(key='last_notice', name='Last Notification', type='datetime', show=True, primary=False),
        IssueProp(key='notes', name='Notes', type='array', show=True, primary=False),
    ]

    # region Object properties
    @property
    def volume(self):
        """Return the volume object for the issue

        Returns:
            `EBSVolume`
        """
        return EBSVolume.get(self.volume_id)
    # endregion

    @deprecated('`update` is deprecated, please use `update_issue` instead')
    def update(self, data):
        """Updates the object information based on live data, if there were any changes made. Any changes will be
        automatically applied to the object, but will not be automatically persisted. You must manually call
        `db.session.add(instance)` on the object.

        Args:
            data (:obj:): AWS API Resource object fetched from AWS API

        Returns:
            `bool`
        """
        # If the instance was terminated, remove it
        updated = self.set_property('state', data['state'])
        updated |= self.set_property('notes', sorted(data['notes'] or []))
        updated |= self.set_property('last_notice', data['last_notice'])

        if updated:
            self.set_property('last_change', datetime.now())

        return updated

    def to_json(self):
        data = super().to_json()
        data['volume'] = self.volume

        return data
