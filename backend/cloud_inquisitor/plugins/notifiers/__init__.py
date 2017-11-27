from abc import abstractmethod, ABC

from cloud_inquisitor.plugins import BasePlugin


class BaseNotifier(BasePlugin, ABC):
    @property
    @abstractmethod
    def name(self): pass

    @property
    @abstractmethod
    def enabled(self): pass

    @property
    @abstractmethod
    def ns(self): pass
