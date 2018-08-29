import logging
from abc import ABC

from cloud_inquisitor.database import db
from cloud_inquisitor.schema import Enforcements, Resource
from sqlalchemy.exc import SQLAlchemyError


class Enforcement(ABC):
    """Base Object for Enforcement Actions"""

    def __init__(self, enforcement):
        self.enforcement = enforcement
        self.log = logging.getLogger(self.__class__.__module__)

    def __getattr__(self, item):
        return self.get_property(item)

    def __str__(self):
        return '<{} enforcement_id={}>'.format(self.__class__.__name__, self.id)

    @classmethod
    def get_one(cls, enforcement_id):
        """ Return the properties of any enforcement action"""

        qry = db.Enforcements.filter(enforcement_id == Enforcements.enforcement_id)
        return qry

    @classmethod
    def get_all(cls, account_id=None, location=None):
        """ Return all Enforcements

        args:
            `account_id` : Unique Account Identifier
            `location` : Region associated with the Resource

        returns:
            list of enforcement objects

        """
        qry = db.Enforcements.filter()

        if account_id:
            qry = qry.filter(account_id == Enforcements.account_id)

        if location:
            qry = qry.join(Resource, Resource.location == location)

        return qry

    @classmethod
    def create(cls, account_id, resource_id, action, timestamp, metrics):
        """ Set properties for an enforcement action"""

        enforcement = Enforcements()
        enforcement.account_id = account_id
        enforcement.resource_id = resource_id
        enforcement.action = action
        enforcement.timestamp = timestamp
        enforcement.metrics = metrics

        try:
            db.session.add(enforcement)

        except SQLAlchemyError as e:
            logging.error('Could not add enforcement entry to database. {}'.format(e))

    @property
    def id(self):
        """ The unique Enforcement ID for the enforcement action

        Returns: `integer`

        """
        return self.enforcement.id

    @property
    def account_id(self):
        """ The Resource ID for the enforcement action

        Returns: `str` : The Resource ID (i.e. instanceID, S3 BucketName)

        """
        return self.enforcement.account_id

    @property
    def resource_id(self):
        """ The Resource ID for the enforcement action

        Returns: `str` : The Resource ID (i.e. instanceID, S3 BucketName)

        """
        return self.enforcement.resource_id

    @property
    def location(self):
        """ The Region for the Resource

        Returns: `str` : The AWS region (i.e. us-west-2)

        """
        return self.enforcement.location

    @property
    def action(self):
        """ The Action taken for the enforcement

        Returns: `str` : Values: (SHUTDOWN, TERMINATED)

        """
        return self.enforcement.action

    @property
    def timestamp(self):
        """ The timestamps for enforcement actions

        Returns: `list` : Values : Timestamps in datetime format

        """
        return self.enforcement.timestamp

    def metrics(self):
        """ The metric data for resources subject to enforcement

        Returns: `json`

        """

        return self.enforcement.metrics
