"""
The core class for the Leek bot.
"""

from __future__ import annotations

import logging
import traceback
from importlib.metadata import version
from pathlib import Path
from typing import Optional

import aiohttp
import aiomysql
from aiohttp.client import _RequestContextManager
from aiomysql import Pool, Connection
from discord import AutoShardedBot, ApplicationContext, DiscordException, Embed, SlashCommand, NotFound

from .localization import localize, get_default, get_localizations

LOGGER = logging.getLogger("leek")


def _is_running_on_docker():
    mountinfo = Path("/proc/1/mountinfo")
    return mountinfo.is_file() and mountinfo.read_text().find("/var/lib/docker/containers/") > -1


class LeekBot(AutoShardedBot):
    """
    The core class for the Leek bot.
    """
    def __init__(self, *args, debug: bool = False, pool_info: Optional[dict] = None, **kwargs):
        """
        Creates a new instance of the Leek bot.
        :param args: The positional arguments that an AutoShardedBot take.
        :param debug: Whether the bot will run with debug mode enabled.
        :param pool_info: The database pool information.
        :param kwargs: The keyword arguments that an AutoShardedBot take.
        """
        if debug:
            LOGGER.warning("Debug mode is enabled, exceptions will be returned to the user")

        if pool_info is None:
            LOGGER.warning("DB Connection not present, some Cogs might not work")

        if pool_info is not None:
            pool_info["minsize"] = 0
            pool_info["maxsize"] = 0
            pool_info["pool_recycle"] = 60.0

        self.__docker = _is_running_on_docker()
        self.__session: Optional[aiohttp.ClientSession] = None
        self.__debug: bool = debug
        self.__pool_info: Optional[dict] = pool_info
        self.__pool: Optional[Pool] = None
        super().__init__(*args, **kwargs)

        command = SlashCommand(self.__about,
                               name=get_default("BOT_COMMAND_ABOUT_NAME"),
                               description=get_default("BOT_COMMAND_ABOUT_DESCRIPTION"),
                               name_localizations=get_localizations("BOT_COMMAND_ABOUT_NAME"),
                               description_localizations=get_localizations("BOT_COMMAND_ABOUT_DESCRIPTION"))
        self.add_application_command(command)

    async def __ensure_sesion(self):
        if self.__session is None:
            self.__session = aiohttp.ClientSession(headers={
                "User-Agent": "Leek/0.0.1"
            })

    @property
    def is_in_docker(self) -> bool:
        """
        Checks if the bot is running on a Docker container.
        """
        return self.__docker

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
    def connection(self) -> Optional[Connection]:
        """
        Gathers a database connection from the pool, if available.
        """
        if not self.is_pool_available:
            return None
        return self.__pool.acquire()

    async def get(self, *args, **kwargs) -> _RequestContextManager:
        """
        Makes a GET request.
        """
        await self.__ensure_sesion()
        return self.__session.get(*args, **kwargs)

    async def post(self, *args, **kwargs) -> _RequestContextManager:
        """
        Makes a POST request.
        """
        await self.__ensure_sesion()
        return self.__session.post(*args, **kwargs)

    async def put(self, *args, **kwargs) -> _RequestContextManager:
        """
        Makes a PUT request.
        """
        await self.__ensure_sesion()
        return self.__session.put(*args, **kwargs)

    async def delete(self, *args, **kwargs) -> _RequestContextManager:
        """
        Makes a DELETE request.
        """
        await self.__ensure_sesion()
        return self.__session.delete(*args, **kwargs)

    async def head(self, *args, **kwargs) -> _RequestContextManager:
        """
        Makes a HEAD request.
        """
        await self.__ensure_sesion()
        return self.__session.head(*args, **kwargs)

    async def options(self, *args, **kwargs) -> _RequestContextManager:
        """
        Makes a OPTIONS request.
        """
        await self.__ensure_sesion()
        return self.__session.options(*args, **kwargs)

    async def patch(self, *args, **kwargs) -> _RequestContextManager:
        """
        Makes a PATCH request.
        """
        await self.__ensure_sesion()
        return self.__session.patch(*args, **kwargs)

    async def on_connect(self):
        """
        Handles the pool connection behavior.
        """
        await super().on_connect()

        if self.__pool_info is not None:
            self.__pool = await aiomysql.create_pool(**self.__pool_info)

    async def on_ready(self):
        """
        Function triggered when the bot is ready.
        """
        LOGGER.info("Bot is Ready to start working!")

    async def on_application_command_error(self, ctx: ApplicationContext, exception: DiscordException):
        """
        Handles the exceptions generated by application commands.
        :param ctx: The context of the command.
        :param exception: The exception that was raised.
        """
        if self.debug:
            info = traceback.format_exception(type(exception), exception, exception.__traceback__)
            text = "\n".join(info)
            message = f"```\n{text}\n```"
        else:
            message = localize("BOT_EXCEPTION_OCURRED", ctx.locale)

        try:
            await ctx.respond(message, ephemeral=True)
        except NotFound:
            await ctx.send(message, delete_after=60)

        await super().on_application_command_error(ctx, exception)

    async def __about(self, ctx: ApplicationContext):
        yes = localize("YES", ctx.locale)
        no = localize("NO", ctx.locale)

        embed = Embed()
        embed.colour = 0x499529
        embed.title = localize("BOT_COMMAND_ABOUT_TITLE", ctx.locale)
        embed.url = "https://github.com/LeekByLemon"
        embed.description = localize("BOT_COMMAND_ABOUT_BODY", ctx.locale)
        embed.set_thumbnail(url="https://avatars.githubusercontent.com/u/99556316")
        embed.set_footer(text=localize("BOT_COMMAND_ABOUT_FOOTER", ctx.locale))

        embed.add_field(name=localize("BOT_COMMAND_ABOUT_VERSION", ctx.locale),
                        value=version("leekbot"),
                        inline=True)
        embed.add_field(name=localize("BOT_COMMAND_ABOUT_DOCKER", ctx.locale),
                        value=yes if self.is_in_docker else no,
                        inline=True)
        embed.add_field(name=localize("BOT_COMMAND_ABOUT_COGS", ctx.locale),
                        value=str(len(self.cogs)),
                        inline=True)

        await ctx.respond(embed=embed)
