from sqlalchemy import Column, String, ForeignKey, DateTime, func
from sqlalchemy.dialects.mysql import INTEGER as Integer

from cloud_inquisitor.database import db, Model
from cloud_inquisitor.schema.base import BaseModelMixin

__all__ = 'EnforcementAction'


class Enforcements(Model, BaseModelMixin):
    """ EnforcementAction Object """
    __tablename__ = "enforcements"
    enforcement_id = Column(Integer(unsigned=True), primary_key=True, autoincrement=True)
    account_id = Column(
        Integer(unsigned=True),
        ForeignKey('accounts.account_id', name='fk_account_properties_account_id', ondelete='CASCADE'))
    resource_id = Column(
        String(256),
        ForeignKey('resources.resource_id', name='fk_tag_resource_id', ondelete='CASCADE'),
        index=True)
    action = Column(String(64))
    timestamp = Column(DateTime(timezone=True), default=func.now())

    @staticmethod
    def get(enforcement_id):
        """Return enforcement by ID

        Args:
            enforcement_id (str): Unique Enforcement identifier

        Returns:
            :obj:`Enforcement`: Returns Enforcement object if found, else None
        """
        return db.EnforcementAction.find_one(
            Enforcements.enforcement_id == enforcement_id
        )

    def __repr__(self):
        return "{}({}, {}, '{}', '{}', '{}')".format(
            self.__class__.__name__,
            self.enforcement_id,
            self.account_id,
            self.resource_id,
            self.action,
            self.timestamp
        )
