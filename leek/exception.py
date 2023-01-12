from discord import Cog


class LeekError(Exception):
    """
    The basic exception for all Leek exceptions.
    """
    pass


class DatabaseRequiredError(LeekError):
    """
    An exception raised when the database pool connection is required but is not available.
    """
    def __init__(self, cog: Cog):
        super().__init__(f"Cog {cog.qualified_name} requires a database connection but is not available")
