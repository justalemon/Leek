"""
Extension to report pings to Hyperping.
"""

import logging
import os

from discord.ext import tasks
from discord.ext.commands import Cog

from leek import LeekBot

LOGGER = logging.getLogger("leek_hyperping")


class Hyperping(Cog):
    """
    Cog used to report pings to Hyperping.
    """
    def __init__(self, bot: LeekBot):
        """
        Creates a new Cog.
        """
        self.bot = bot
        self.url = os.environ.get("HYPERPING_URL", None)

        if self.url is None:
            LOGGER.error("No Hyperping URL specified, no Pings will be sent!")

        self.ping.start()

    async def send_ping(self) -> bool:
        """
        Sends a ping to Hyperping.
        """
        if self.url is None:
            return False

        async with await self.bot.head(self.url) as resp:
            return resp.ok

    @tasks.loop(seconds=float(os.environ.get("HYPERPING_DELAY", "60.0")))
    async def ping(self) -> None:
        """
        Sends the ping every couple of seconds.
        """
        success = await self.send_ping()

        if success:
            LOGGER.info("Successful report to Hyperping")
        else:
            LOGGER.error("Unable to report to Hyperping, check Hyperping for more information")
