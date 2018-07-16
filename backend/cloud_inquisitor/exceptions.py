class InquisitorError(Exception):
    pass


class CloudFlareError(InquisitorError):
    pass


class EmailSendError(InquisitorError):
    pass


class ObjectDeserializationError(InquisitorError):
    pass


class SlackError(InquisitorError):
    pass


class ResourceException(InquisitorError):
    """Exception class for resource types"""


class IssueException(InquisitorError):
    """Exception class for issue types"""


class AccountException(InquisitorError):
    """Exception class for Account types"""


class SchedulerError(InquisitorError):
    """Exception class for scheduler plugins"""
