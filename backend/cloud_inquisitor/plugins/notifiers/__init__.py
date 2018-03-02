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

    @abstractmethod
    def notify(self, subsystem, recipient, subject, body_html, body_text):
        """Method to send a notification. A plugin may use only part of the information, but all fields are required.

        Args:
            subsystem (`str`): Name of the subsystem originating the notification
            recipient (`str`): Recipient of the notification
            subject (`str`): Subject / title of the notification
            body_html (`str)`: HTML formatted version of the message
            body_text (`str`): Text formatted version of the message

        Returns:
            `None`
        """

    @property
    @abstractmethod
    def notifier_type(self):
        """A string used to identify the type of contact"""

    @abstractmethod
    def validation(self):
        """A regular expression used to validate if a contact is correctly formatted for the notifier"""
