from __future__ import annotations

from typing import Optional

import aiomysql
from aiomysql import Pool
from discord import AutoShardedBot


class LeekBot(AutoShardedBot):
    def __init__(self, *args, pool_info: Optional[dict] = None, **kwargs):
        if pool_info is None:
            pool_info = {}

        pool_info["minsize"] = 0
        pool_info["maxsize"] = 0
        pool_info["pool_recycle"] = 60.0

        self.__pool_info: dict = pool_info
        self.__pool: Optional[Pool] = None
        super().__init__(*args, **kwargs)

    async def on_connect(self):
        await super().on_connect()
        self.__pool = await aiomysql.create_pool(**self.__pool_info)
