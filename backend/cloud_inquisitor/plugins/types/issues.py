import logging
from abc import abstractmethod, ABC
from datetime import datetime

from sqlalchemy import or_, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased

from cloud_inquisitor.database import db
from cloud_inquisitor.exceptions import IssueException
from cloud_inquisitor.plugins.types.resources import EC2Instance, EBSVolume
from cloud_inquisitor.schema import IssueProperty, Issue, IssueType
from cloud_inquisitor.utils import to_camelcase, parse_date


class BaseIssue(ABC):
    """Base type object for issue objects"""
    def __init__(self, issue):
        self.issue = issue
        self.log = logging.getLogger(self.__class__.__module__)

    def __getattr__(self, item):
        return self.get_property(item)

    def __str__(self):
        return '<{} issue_id={}>'.format(self.__class__.__name__, self.id)

    def get_property(self, item):
        for prop in self.issue.properties:
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

    @abstractmethod
    def update(self, data):
        """Updates the issue object with the information from `data`. The changes will be added to the current
        db.session but will not be commited. The user will need to perform the commit explicitly to save the changes

        Returns:
            True if issue object was updated, else False
        """

    # region Class methods
    @classmethod
    def get(cls, issue_id):
        """Returns the class object identified by `issue_id`

        Args:
            issue_id (str): Unique EC2 Instance ID to load from database

        Returns:
            EC2 Instance object if found, else None
        """
        res = Issue.get(issue_id, IssueType.get(cls.issue_type).issue_type_id)
        return cls(res) if res else None

    @classmethod
    def create(cls, issue_id, *, properties=None, auto_commit=False):
        """Creates a new Issue object with the properties and tags provided

        Attributes:
            issue_id (str): Unique identifier for the issue object
            account (:obj:`Account`): Account which owns the issue
            properties (dict): Dictionary of properties for the issue object.
        """
        if cls.get(issue_id):
            raise IssueException('Issue {} already exists'.format(issue_id))

        res = Issue()
        res.issue_id = issue_id
        res.issue_type_id = IssueType.get(cls.issue_type).issue_type_id

        if properties:
            for name, value in properties.items():
                prop = IssueProperty()
                prop.issue_id = res.issue_id
                prop.name = name
                prop.value = value.isoformat() if type(value) == datetime else value
                res.properties.append(prop)
                db.session.add(prop)

        db.session.add(res)
        if auto_commit:
            db.session.commit()

        return cls.get(res.issue_id)

    @classmethod
    def get_all(cls):
        """Returns a list of all issues of a given type

        Returns:
            list of issue objects
        """
        issues = db.Issue.find(
            Issue.issue_type_id == IssueType.get(cls.issue_type).issue_type_id
        )

        return {res.issue_id: cls(res) for res in issues}

    @classmethod
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
    # endregion


class RequiredTagsIssue(BaseIssue):
    """Issue type for instances missing required tags"""
    issue_type = 'aws_required_tags'
    issue_name = 'Required Tags Issue'

    # region Object properties
    @property
    def instance_id(self):
        """Returns the EC2 Instance ID that has issues

        Returns:
            `str`
        """
        return self.get_property('instance_id').value

    @property
    def account_id(self):
        """The account ID of the account where the issue is present

        Returns:
            `int`
        """
        return self.get_property('account_id').value

    @property
    def location(self):
        """The AWS Region the instance resides in

        Returns:
            `str`
        """
        return self.get_property('location').value

    @property
    def state(self):
        """Returns the current state of the issue

        Returns:
            `int`
        """
        return self.get_property('state').value

    @property
    def last_change(self):
        """Returns a `datetime` object, showing the last time changes were detected on the issue, or `None` if not set

        Returns:
            `datetime`,`None`
        """
        return parse_date(self.get_property('last_change').value)

    @property
    def next_change(self):
        """Returns the `datetime` of the next change to the object, or None if not set

        Returns:
            `datetime`,`None`
        """
        return parse_date(self.get_property('next_change').value)

    @property
    def shutdown_on(self):
        """Returns the `datetime` the instance will be shutdown if not fixed, or None if not set

        Returns:
            `datetime`,`None`
        """
        return parse_date(self.get_property('shutdown_on').value)

    @property
    def missing_tags(self):
        """Returns a `list` of key names for missing or invalid tags on the instance

        Returns:
            `list` of `str`
        """
        return self.get_property('missing_tags').value

    @property
    def notes(self):
        """Return a list of notes for the issue (optional)

        Returns:
            `list` of `str`
        """
        return self.get_property('notes').value

    @property
    def instance(self):
        """Return the instance object for the issue

        Returns:
            `EC2Instance`
        """
        return EC2Instance.get(self.instance_id)
    # endregion

    def update(self, data):
        """Updates the object information based on live data, if there were any changes made. Any changes will be
        automatically applied to the object, but will not be automatically persisted. You must manually call
        `db.session.add(instance)` on the object.

        Args:
            data (:obj:): AWS API Resource object fetched from AWS API

        Returns:
            `bool`
        """
        updated = self.set_property('missing_tags', data['missing_tags'])
        updated |= self.set_property('notes', data['notes'])
        updated |= self.set_property('state', data['state'])

        if updated:
            now = datetime.now()
            self.set_property('last_change', now)
            self.set_property('next_change', now + data['next_change'])

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
        data['instance'] = self.instance

        return data


class DomainHijackIssue(BaseIssue):
    """Domain Hijacking Issue"""
    issue_type = 'domain_hijacking'
    issue_name = 'Domain Hijacking Issue'

    # region Object properties
    @property
    def issue_hash(self):
        """Unique issue hash for the issue, used for tracking changes

        Returns:
            `str`
        """
        return self.get_property('issue_hash').value

    @property
    def source(self):
        """Source location of the issue

        Returns:
            `str`
        """
        return self.get_property('source').value

    @property
    def description(self):
        """Description of the issue

        Returns:
            `str`
        """
        return self.get_property('description').value

    @property
    def state(self):
        """Current state of the issue

        Returns:
            `str`
        """
        return self.get_property('state').value

    @property
    def start(self):
        """Returns the `datetime` of when the issue was detected, or None if not set

        Returns:
            `datetime`,`None`
        """
        return parse_date(self.get_property('start').value)

    @property
    def end(self):
        """Returns the `datetime` of when the issue was fixed, or `None` if not set

        Returns:
            `datetime`,`None`
        """
        return parse_date(self.get_property('end').value)
    # endregion

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
        updated |= self.set_property('end', data['end'])

        return updated


class EBSVolumeAuditIssue(BaseIssue):
    """EBSVolume audit issue"""
    issue_type = 'aws_ebs_volume_audit'
    issue_name = 'EBS Volume Audit Issue'

    # region Object properties
    @property
    def volume_id(self):
        """Returns the resource ID of the volume

        Returns:
            `str`
        """
        return self.get_property('volume_id')

    @property
    def state(self):
        """Current state of the issue

        Returns:
            `str`
        """
        return self.get_property('state').value

    @property
    def last_change(self):
        """Returns the `datetime` of when the issue was last updated, or `None` if not set

        Returns:
            `datetime`,`None`
        """
        return parse_date(self.get_property('last_change').value)

    @property
    def last_notice(self):
        """Returns the `datetime` of when the issue was last notified, or `None` if not set

        Returns:
            `datetime`,`None`
        """
        return parse_date(self.get_property('last_notice').value)

    @property
    def notes(self):
        """Returns any notes associated with the issue

        Returns:
            `list` of `str`
        """
        return self.get_property('notes').value

    @property
    def volume(self):
        """Return the volume object for the issue

        Returns:
            `EBSVolume`
        """
        return EBSVolume.get(self.get_property('volume_id').value)
    # endregion

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
