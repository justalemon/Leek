"""
Extension used to create and manage tags.
"""

from typing import TYPE_CHECKING

import discord
from pymysql import IntegrityError

from leek import DatabaseRequiredError, LeekBot, d, l, la

if TYPE_CHECKING:
    from aiomysql import Cursor

PERMISSIONS = discord.Permissions(manage_messages=True)
CREATE = "CREATE TABLE IF NOT EXISTS tags_%s (id INT NOT NULL auto_increment, name TEXT NOT NULL UNIQUE, " \
         "content TEXT NOT NULL, primary key (id))"
FETCH_ALL = "SELECT (name) FROM tags_%s"
FETCH_SINGLE = "SELECT (content) FROM tags_%s WHERE name=%s"
ADD = "INSERT INTO tags_%s (name, content) VALUES (%s, %s)"
DELETE = "DELETE FROM tags_%s WHERE name=%s"


async def get_tag_names(ctx: discord.AutocompleteContext) -> list[str]:
    """
    Gets the tag names used for the autocomplete feature.
    """
    if not isinstance(ctx.bot, LeekBot):
        return []

    bot: LeekBot = ctx.bot

    if not bot.is_pool_available:
        return []

    async with bot.connection as connection:
        cursor: Cursor = await connection.cursor()
        await cursor.execute(CREATE, [ctx.interaction.guild.id])
        await cursor.execute(FETCH_ALL, [ctx.interaction.guild.id])
        await connection.commit()
        tags = await cursor.fetchall()
        await cursor.close()
        return [x[0] for x in tags]


class Tags(discord.Cog):
    """
    Cog used to create and manage Tags.
    """
    def __init__(self, bot: LeekBot):
        """
        Creates a new Tags Cog.
        """
        self.bot: LeekBot = bot

    async def cog_before_invoke(self, ctx: discord.ApplicationContext) -> None:  # noqa: ARG002
        """
        Checks whether the database is available before executing a command.
        """
        if not self.bot.is_pool_available:
            raise DatabaseRequiredError(self)

    @discord.slash_command(name_localizations=la("COMMAND_TAG_NAME"),
                           description=d("COMMAND_TAG_DESC"),
                           description_localization=la("COMMAND_TAG_DESC"))
    @discord.option(type=discord.SlashCommandOptionType.string,
                    name=d("COMMAND_TAG_NAME_NAME"),
                    name_localizations=la("COMMAND_TAG_NAME_NAME"),
                    description=d("COMMAND_TAG_NAME_DESC"),
                    description_localizations=la("COMMAND_TAG_NAME_DESC"),
                    autocomplete=get_tag_names)
    async def tag(self, ctx: discord.ApplicationContext, name: str) -> None:
        """
        Gets a specific tag.
        """
        async with self.bot.connection as connection:
            cursor: Cursor = await connection.cursor()
            await cursor.execute(CREATE, [ctx.interaction.guild.id])
            await cursor.execute(FETCH_SINGLE, [ctx.interaction.guild.id, name])
            await connection.commit()
            tag = await cursor.fetchone()
            await cursor.close()

        if tag is None:
            await ctx.respond(l("NOT_FOUND", ctx.locale, name), ephemeral=True)
        else:
            await ctx.respond(tag[0])

    @discord.slash_command(name_localizations=la("COMMAND_CREATETAG_NAME"),
                           description=d("COMMAND_CREATETAG_DESC"),
                           description_localization=la("COMMAND_CREATETAG_DESC"),
                           default_member_permissions=PERMISSIONS)
    @discord.option(type=discord.SlashCommandOptionType.string,
                    name=d("COMMAND_CREATETAG_NAME_NAME"),
                    name_localizations=la("COMMAND_CREATETAG_NAME_NAME"),
                    description=d("COMMAND_CREATETAG_NAME_DESC"),
                    description_localizations=la("COMMAND_CREATETAG_NAME_DESC"))
    @discord.option(type=discord.SlashCommandOptionType.string,
                    name=d("COMMAND_CREATETAG_CONTENT_NAME"),
                    name_localizations=la("COMMAND_CREATETAG_CONTENT_NAME"),
                    description=d("COMMAND_CREATETAG_CONTENT_DESC"),
                    description_localizations=la("COMMAND_CREATETAG_CONTENT_DESC"))
    async def createtag(self, ctx: discord.ApplicationContext, name: str, content: str) -> None:
        """
        Creates a new tag.
        """
        try:
            async with self.bot.connection as connection:
                cursor: Cursor = await connection.cursor()
                await cursor.execute(CREATE, [ctx.interaction.guild.id])
                await cursor.execute(ADD, [ctx.interaction.guild.id, name, content])
                await connection.commit()
                await cursor.close()
                await ctx.respond(l("ADD_OKAY", ctx.locale, name), ephemeral=True)
        except IntegrityError:
            await ctx.respond(l("ADD_DUPE", ctx.locale, name), ephemeral=True)

    @discord.slash_command(name_localizations=la("COMMAND_DELETETAG_NAME"),
                           description=d("COMMAND_DELETETAG_DESC"),
                           description_localization=la("COMMAND_DELETETAG_DESC"),
                           default_member_permissions=PERMISSIONS)
    @discord.option(type=discord.SlashCommandOptionType.string,
                    name=d("COMMAND_DELETETAG_NAME_NAME"),
                    name_localizations=la("COMMAND_DELETETAG_NAME_NAME"),
                    description=d("COMMAND_DELETETAG_NAME_DESC"),
                    description_localizations=la("COMMAND_DELETETAG_NAME_DESC"))
    async def deletetag(self, ctx: discord.ApplicationContext, name: str) -> None:
        """
        Deletes a specific tag by it's name.
        """
        async with self.bot.connection as connection:
            cursor: Cursor = await connection.cursor()
            await cursor.execute(CREATE, [ctx.interaction.guild.id])
            await cursor.execute(DELETE, [ctx.interaction.guild.id, name])
            await connection.commit()
            rows = cursor.rowcount
            await cursor.close()

        if rows == 0:
            await ctx.respond(l("NOT_FOUND", ctx.locale, name), ephemeral=True)
        else:
            await ctx.respond(l("DELETE_OKAY", ctx.locale, name), ephemeral=True)
