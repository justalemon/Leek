from __future__ import annotations

import logging
from typing import Optional

import aiomysql
from aiomysql import Pool
from discord import AutoShardedBot
from discord.ext.commands import Context

LOGGER = logging.getLogger("leek")


class LeekBot(AutoShardedBot):
    def __init__(self, *args, debug: bool = False, pool_info: Optional[dict] = None, **kwargs):
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
