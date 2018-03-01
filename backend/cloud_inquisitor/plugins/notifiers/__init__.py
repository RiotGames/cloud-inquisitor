from abc import abstractmethod, ABC

from cloud_inquisitor.config import dbconfig
from cloud_inquisitor.plugins import BasePlugin


class BaseNotifier(BasePlugin, ABC):
    @classmethod
    def enabled(cls):
        return dbconfig.get('enabled', cls.ns, False)

    @property
    @abstractmethod
    def name(self): pass

    @property
    @abstractmethod
    def ns(self): pass
