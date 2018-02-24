import logging
from abc import abstractmethod, ABC

from flask_script import Command

from cloud_inquisitor.plugins import BasePlugin


class BaseCommand(BasePlugin, Command, ABC):
    def __init__(self):
        super().__init__()
        self.log = logging.getLogger(self.__class__.__module__)

    @abstractmethod
    def run(self, **kwargs): pass

    @property
    @abstractmethod
    def name(self): pass
