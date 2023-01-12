from __future__ import annotations

import logging
import traceback
from typing import Optional

import aiohttp
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
            LOGGER.warning("DB Connection not present, some Cogs might not work")

        if pool_info is not None:
            pool_info["minsize"] = 0
            pool_info["maxsize"] = 0
            pool_info["pool_recycle"] = 60.0

        self.__session: Optional[aiohttp.ClientSession] = None
        self.__debug: bool = debug
        self.__pool_info: Optional[dict] = pool_info
        self.__pool: Optional[Pool] = None
        super().__init__(*args, **kwargs)

    async def __ensure_sesion(self):
        if self.__session is None:
            self.__session = aiohttp.ClientSession(headers={
                "User-Agent": "Leek/0.0.1"
            })

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

    async def get(self, *args, **kwargs):
        """
        Makes a GET request.
        """
        await self.__ensure_sesion()
        return await self.__session.get(*args, **kwargs)

    async def post(self, *args, **kwargs):
        """
        Makes a POST request.
        """
        await self.__ensure_sesion()
        return await self.__session.post(*args, **kwargs)

    async def put(self, *args, **kwargs):
        """
        Makes a PUT request.
        """
        await self.__ensure_sesion()
        return await self.__session.put(*args, **kwargs)

    async def delete(self, *args, **kwargs):
        """
        Makes a DELETE request.
        """
        await self.__ensure_sesion()
        return await self.__session.delete(*args, **kwargs)

    async def head(self, *args, **kwargs):
        """
        Makes a HEAD request.
        """
        await self.__ensure_sesion()
        return await self.__session.head(*args, **kwargs)

    async def options(self, *args, **kwargs):
        """
        Makes a OPTIONS request.
        """
        await self.__ensure_sesion()
        return await self.__session.options(*args, **kwargs)

    async def patch(self, *args, **kwargs):
        """
        Makes a PATCH request.
        """
        await self.__ensure_sesion()
        return await self.__session.patch(*args, **kwargs)

    async def on_connect(self):
        await super().on_connect()

        if self.__pool_info is not None:
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
