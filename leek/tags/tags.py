"""
Extension used to create and manage tags.
"""

from typing import TYPE_CHECKING

from discord import ApplicationContext, AutocompleteContext, Cog, Option, Permissions, slash_command
from pymysql import IntegrityError

from leek import DatabaseRequiredError, LeekBot, get_default, get_localizations, localize

if TYPE_CHECKING:
    from aiomysql import Cursor

PERMISSIONS = Permissions(manage_messages=True)
CREATE = "CREATE TABLE IF NOT EXISTS tags_%s (id INT NOT NULL auto_increment, name TEXT NOT NULL UNIQUE, " \
         "content TEXT NOT NULL, primary key (id))"
FETCH_ALL = "SELECT (name) FROM tags_%s"
FETCH_SINGLE = "SELECT (content) FROM tags_%s WHERE name=%s"
ADD = "INSERT INTO tags_%s (name, content) VALUES (%s, %s)"
DELETE = "DELETE FROM tags_%s WHERE name=%s"


async def get_tag_names(ctx: AutocompleteContext) -> list[str]:
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


class Tags(Cog):
    """
    Cog used to create and manage Tags.
    """
    def __init__(self, bot: LeekBot):
        """
        Creates a new Tags Cog.
        """
        self.bot: LeekBot = bot

    async def cog_before_invoke(self, ctx: ApplicationContext) -> None:  # noqa: ARG002
        """
        Checks whether the database is available before executing a command.
        """
        if not self.bot.is_pool_available:
            raise DatabaseRequiredError(self)

    @slash_command(name_localizations=get_localizations("TAGS_COMMAND_TAG_NAME"),
                   description=get_default("TAGS_COMMAND_TAG_DESC"),
                   description_localization=get_localizations("TAGS_COMMAND_TAG_DESC"))
    async def tag(self, ctx: ApplicationContext, name: Option(str, "The tag name", autocomplete=get_tag_names)) -> None:
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
            await ctx.respond(localize("TAGS_NOT_FOUND", ctx.locale, name), ephemeral=True)
        else:
            await ctx.respond(tag[0])

    @slash_command(name_localizations=get_localizations("TAGS_COMMAND_CREATETAG_NAME"),
                   description=get_default("TAGS_COMMAND_CREATETAG_DESC"),
                   description_localization=get_localizations("TAGS_COMMAND_CREATETAG_DESC"),
                   default_member_permissions=PERMISSIONS)
    async def createtag(self, ctx: ApplicationContext, name: Option(str, "The tag name"),
                        content: Option(str, "The text content of the tag")) -> None:
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
                await ctx.respond(localize("TAGS_ADD_OKAY", ctx.locale, name), ephemeral=True)
        except IntegrityError:
            await ctx.respond(localize("TAGS_ADD_DUPE", ctx.locale, name), ephemeral=True)

    @slash_command(name_localizations=get_localizations("TAGS_COMMAND_DELETETAG_NAME"),
                   description=get_default("TAGS_COMMAND_DELETETAG_DESC"),
                   description_localization=get_localizations("TAGS_COMMAND_DELETETAG_DESC"),
                   default_member_permissions=PERMISSIONS)
    async def deletetag(self, ctx: ApplicationContext, name: Option(str, "The tag name",
                                                                    autocomplete=get_tag_names)) -> None:
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
            await ctx.respond(localize("TAGS_NOT_FOUND", ctx.locale, name), ephemeral=True)
        else:
            await ctx.respond(localize("TAGS_DELETE_OKAY", ctx.locale, name), ephemeral=True)
