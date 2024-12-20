"""
Moderation tools for the Leek bot.
"""

import asyncio
import logging
from typing import Optional

from discord import (
    ApplicationContext,
    Cog,
    Forbidden,
    HTTPException,
    Message,
    NotFound,
    Permissions,
    Role,
    option,
    slash_command,
)

from leek import LeekBot, d, l, la

LOGGER = logging.getLogger("leek_moderation")
PERMISSIONS_MESSAGES = Permissions(manage_messages=True)
PERMISSIONS_ADMIN = Permissions(administrator=True)


class Moderation(Cog):
    """
    Set of tools for the Moderation of Discord servers.
    """
    def __init__(self, bot: LeekBot):
        """
        Creates a new moderation cog.
        :param bot: The bot instance to use.
        """
        self.bot: LeekBot = bot

    async def _safely_delete(self, ctx: ApplicationContext, message: Message) -> bool:
        try:
            await message.delete(reason=f"Clear by {ctx.user} ({ctx.user})")
        except Forbidden:
            await ctx.send(l("COMMAND_CLEAR_NO_PERMS", ctx.locale))
            return False
        except NotFound:
            return True
        except HTTPException as e:
            if e.code != 429:
                await ctx.send(l("COMMAND_CLEAR_HTTP_ERROR", ctx.locale, e.code))
                return False

            response = await e.response.json()
            retry = response["retry_after"]

            if response["global"]:
                await ctx.send(l("COMMAND_CLEAR_LIMIT_GLOBAL", ctx.locale, retry))
                return False

            await ctx.send(l("COMMAND_CLEAR_LIMIT_LOCAL", ctx.locale, retry),
                           delete_after=10)
            await asyncio.sleep(retry + 1)
            return await self._safely_delete(ctx, message)
        else:
            return True

    @slash_command(name=d("COMMAND_CLEAR_NAME"),
                   name_localizations=la("COMMAND_CLEAR_NAME"),
                   description=d("COMMAND_CLEAR_HELP"),
                   description_localizations=la("COMMAND_CLEAR_HELP"),
                   default_member_permissions=PERMISSIONS_MESSAGES)
    async def clear(self, ctx: ApplicationContext, keep: Optional[str]) -> None:
        """
        Clears the messages of a channel.
        :param ctx: The context of the application.
        :param keep: The id of the message that should stay.
        """
        if keep is not None:
            try:
                keep_id = int(keep)
            except ValueError:
                await ctx.respond(l("COMMAND_CLEAR_INVALID", ctx.locale, keep), ephemeral=True)
                return
        else:
            keep_id = 0

        await ctx.defer(ephemeral=True)

        def should_keep(msg: Message):  # noqa: ANN202
            return msg.id == keep_id

        async for message in ctx.channel.history(limit=100):
            if should_keep(message):
                continue
            await self._safely_delete(ctx, message)

        await ctx.followup.send(l("COMMAND_CLEAR_DONE", ctx.locale), ephemeral=True)

    @slash_command(name_localizations=la("COMMAND_APPLYROLE_NAME"),
                   description=d("COMMAND_APPLYROLE_DESC"),
                   description_localizations=la("COMMAND_APPLYROLE_DESC"),
                   default_member_permissions=PERMISSIONS_ADMIN)
    @option(name=d("COMMAND_APPLYROLE_ROLE_NAME"),
            name_localizations=la("COMMAND_APPLYROLE_ROLE_NAME"),
            description=d("COMMAND_APPLYROLE_ROLE_DESC"),
            description_localizations=la("COMMAND_APPLYROLE_ROLE_DESC"))
    async def applyrole(self, ctx: ApplicationContext, role: Role) -> None:
        """
        Applies a specific role to users that don't have any roles.
        """
        await ctx.defer(ephemeral=True)

        count = 0
        errors = 0

        for member in ctx.guild.members:
            try:
                if member.top_role.name == "@everyone":
                    await member.add_roles(role)
                    count += 1
            except:  # noqa: E722
                errors += 1

        await ctx.respond(l("COMMAND_APPLYROLE_ROLE_COMPLETED", ctx.locale, count, errors))
