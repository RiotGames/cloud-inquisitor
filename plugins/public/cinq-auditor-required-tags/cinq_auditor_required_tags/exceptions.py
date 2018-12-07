from cloud_inquisitor.exceptions import InquisitorError


class ResourceActionError(InquisitorError):
    pass


class ResourceKillError(ResourceActionError):
    pass


class ResourceStopError(ResourceActionError):
    pass
