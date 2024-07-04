"""
The exceptions that are triggered from Leek.
"""

from discord import Cog


class LeekError(Exception):
    """
    The basic exception for all Leek exceptions.
    """


class DatabaseRequiredError(LeekError):
    """
    An exception raised when the database pool connection is required but is not available.
    """
    def __init__(self, cog: Cog):
        """
        Creates a new exception.
        :param cog: The cog that requires the database connection.
        """
        super().__init__(f"Cog {cog.qualified_name} requires a database connection but is not available")


class MissingFeatureError(LeekError):
    """
    An exception raised when a specific system feature or library is missing and is required.
    """
