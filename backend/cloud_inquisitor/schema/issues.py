from sqlalchemy import Column, String
from sqlalchemy.dialects.mysql import INTEGER as Integer, JSON
from sqlalchemy.orm import foreign, relationship

from cloud_inquisitor.database import db, Model
from cloud_inquisitor.schema.base import BaseModelMixin

__all__ = ('IssueType', 'IssueProperty', 'Issue')


class IssueType(Model, BaseModelMixin):
    """Issue type object

    Attributes:
        issue_type_id (int): Unique issue type identifier
        issue_type (str): Issue type name
    """
    __tablename__ = 'issue_types'

    issue_type_id = Column(Integer(unsigned=True), primary_key=True, autoincrement=True)
    issue_type = Column(String(100), nullable=False, index=True)

    @classmethod
    def get(cls, issue_type):
        """Returns the IssueType object for `issue_type`. If no existing object was found, a new type will
        be created in the database and returned

        Args:
            issue_type (str,int,IssueType): Issue type name, id or class

        Returns:
            :obj:`IssueType`
        """
        if isinstance(issue_type, str):
            obj = getattr(db, cls.__name__).find_one(cls.issue_type == issue_type)

        elif isinstance(issue_type, int):
            obj = getattr(db, cls.__name__).find_one(cls.issue_type_id == issue_type)

        elif isinstance(issue_type, cls):
            return issue_type

        else:
            obj = None

        if not obj:
            obj = cls()
            obj.issue_type = issue_type

            db.session.add(obj)
            db.session.commit()
            db.session.refresh(obj)

        return obj


class IssueProperty(Model, BaseModelMixin):
    """Issue Property object"""
    __tablename__ = 'issue_properties'

    property_id = Column(Integer(unsigned=True), primary_key=True, autoincrement=True)
    issue_id = Column(String(256), nullable=False, primary_key=True, index=True)
    name = Column(String(50), nullable=False, index=True)
    value = Column(JSON, nullable=False)

    def __str__(self):
        return self.value

    def __repr__(self):
        return "{}({}, '{}', '{}', '{}')".format(
            self.__class__.__name__,
            self.property_id,
            self.issue_id,
            self.name,
            self.value
        )


class Issue(Model, BaseModelMixin):
    """Issue object

    Attributes:
        issue_id (str): Unique Issue identifier
        issue_type (str): :obj:`IssueType` reference
        properties (`list` of :obj:`IssueProperty`): List of properties of the issue
    """
    __tablename__ = 'issues'

    issue_id = Column(String(256), primary_key=True)
    issue_type_id = Column(Integer(unsigned=True), index=True)
    properties = relationship(
        'IssueProperty',
        lazy='select',
        uselist=True,
        primaryjoin=issue_id == foreign(IssueProperty.issue_id),
        cascade='all, delete-orphan'
    )

    @staticmethod
    def get(issue_id, issue_type_id):
        """Return issue by ID

        Args:
            issue_id (str): Unique Issue identifier
            issue_type_id (str): Type of issue to get

        Returns:
            :obj:`Issue`: Returns Issue object if found, else None
        """
        return db.Issue.find_one(
            Issue.issue_id == issue_id,
            Issue.issue_type_id == issue_type_id
        )
