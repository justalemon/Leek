class LeekError(Exception):
    """
    The basic exception for all Leek exceptions.
    """
    pass


class DatabaseRequiredError(LeekError):
    """
    An exception raised when the database pool connection is required but is not available.
    """
    pass
