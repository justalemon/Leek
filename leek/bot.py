from __future__ import annotations

import logging
import traceback
from typing import Optional

import aiomysql
from aiomysql import Pool
from discord import AutoShardedBot, ApplicationContext, DiscordException

from .localization import localize

LOGGER = logging.getLogger("leek")


class LeekBot(AutoShardedBot):
    def __init__(self, *args, debug: bool = False, pool_info: Optional[dict] = None, **kwargs):
        if debug:
            LOGGER.warning("Debug mode is enabled, exceptions will be returned to the user")

        if pool_info is None:
            pool_info = {}

        pool_info["minsize"] = 0
        pool_info["maxsize"] = 0
        pool_info["pool_recycle"] = 60.0

        self.__debug: bool = debug
        self.__pool_info: dict = pool_info
        self.__pool: Optional[Pool] = None
        super().__init__(*args, **kwargs)

    @property
    def debug(self):
        """
        If debug mode is enabled. Debug mode writes the raw exceptions to Discord instead of showing an error message.
        """
        return self.__debug

    @property
    def is_pool_available(self):
        """
        If the database pool is available.
        """
        return self.__pool is not None

    @property
    def connection(self):
        """
        Gathers a database connection from the pool, if available.
        """
        if not self.is_pool_available:
            return None
        return self.__pool.acquire()

    async def on_connect(self):
        await super().on_connect()
        self.__pool = await aiomysql.create_pool(**self.__pool_info)

    async def on_ready(self):
        LOGGER.info("Bot is Ready to start working!")

    async def on_application_command_error(self, ctx: ApplicationContext, exception: DiscordException):
        if self.debug:
            info = traceback.format_exception(type(exception), exception, exception.__traceback__)
            text = "\n".join(info)
            await ctx.respond(f"```\n{text}\n```", ephemeral=True)
        else:
            await ctx.respond(localize("BOT_EXCEPTION_OCURRED", ctx.locale), ephemeral=True)

        await super().on_application_command_error(ctx, exception)
