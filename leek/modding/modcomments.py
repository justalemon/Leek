"""
Cog for parsing comments from 5mods mod pages and sending them to channels.
"""

import os
import re
from typing import TYPE_CHECKING

import discord
from discord.ext import tasks
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from leek import DatabaseRequiredError, LeekBot, d, l, la

if TYPE_CHECKING:
    from aiomysql import Cursor

PERMISSIONS = discord.Permissions(manage_messages=True)
COLOR = 0x20ba4e
RE_LINK = re.compile("https://www.gta5-mods.com/(tools|vehicles|paintjobs|weapons|scripts|player|maps|misc)"
                     "/([a-z0-9\\-]+)")
XPATH_ERROR = "//div[@class='dialog container']/div/h1"
XPATH_COMMENTS = "//li[@class='comment media ']"
XPATH_MOD_TITLE = "//div[@class='clearfix']/h1"
XPATH_COMMENT_TEXT = ".//div[@class='comment-text ']/p"
XPATH_COMMENT_AUTHOR = ".//div[@class='pull-left flip']/a"
XPATH_COMMENT_IMAGE = ".//img[@class='media-object']"
SQL_CREATE = """CREATE TABLE IF NOT EXISTS mods (
    id INT NOT NULL AUTO_INCREMENT,
    type TEXT NOT NULL,
    slug TEXT NOT NULL,
    guild BIGINT NOT NULL,
    channel BIGINT NOT NULL,
    last INT DEFAULT 0,
    PRIMARY KEY (id)
)"""
SQL_FETCH_ALL = "SELECT * FROM mods"
SQL_FETCH_ONE = "SELECT channel FROM mods WHERE type = %s AND slug = %s AND guild = %s"
SQL_FETCH_GUILD = "SELECT id, type, slug, channel FROM mods WHERE guild = %s"
SQL_INSERT = "INSERT INTO mods (type, slug, guild, channel) VALUES (%s, %s, %s, %s)"


async def _send_message_to(channel: discord.TextChannel, element: WebElement, title: str, url: str) -> None:
    text = element.find_element(By.XPATH, XPATH_COMMENT_TEXT).get_attribute("innerText")
    author = element.find_element(By.XPATH, XPATH_COMMENT_AUTHOR).get_attribute("href").split("/")[-1]
    comment_id = element.get_attribute("data-comment-id")
    image_url = element.find_element(By.XPATH, XPATH_COMMENT_IMAGE).get_attribute("src")

    embed = discord.Embed(color=COLOR, description=text,
                          author=discord.EmbedAuthor(
                              l("MODCOMMENTS_TASK_CHECK_NEW", channel.guild.preferred_locale, title, author),
                              f"{url}#comment-{comment_id}"))
    embed.set_thumbnail(url=image_url)
    embed.set_footer(text="5mods", icon_url="https://images.gta5-mods.com/icons/favicon.png")

    await channel.send(embed=embed)


class ModComments(discord.Cog):
    """
    Comment parser and redirector for 5mods.
    """

    def __init__(self, bot: LeekBot):
        """
        Creates a new Cog.
        """
        desired_driver = os.environ.get("MODCOMMENTS_DRIVER", "firefox").lower()
        headless = bool(int(os.environ.get("MODCOMMENTS_HEADLESS", 1)))

        if desired_driver == "firefox":
            options = FirefoxOptions()
            if headless:
                options.add_argument("--headless")
            self.driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        elif desired_driver == "chrome":
            options = ChromeOptions()
            if headless:
                options.add_argument("--headless=new")
            self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        else:
            raise ValueError(f"Unrecognized driver: {desired_driver}")  # noqa: TRY003

        self.driver.get("https://www.gta5-mods.com")

        self.bot: LeekBot = bot

    async def _update(self, entry_id: int, latest: int) -> None:
        async with self.bot.connection as connection, await connection.cursor() as cursor:
            cursor: Cursor
            await cursor.execute("UPDATE mods SET last = %s WHERE id = %s", (latest, entry_id))
            await connection.commit()

    async def cog_before_invoke(self, ctx: discord.ApplicationContext) -> None:  # noqa: ARG002
        """
        Checks whether the database is available before executing a command.
        """
        if not self.bot.is_pool_available:
            raise DatabaseRequiredError(self)

    @tasks.loop(minutes=int(os.environ.get("MODCOMMENTS_DELAY", 1)))
    async def check_for_comments(self) -> None:
        """
        Task that checks for new comments in a specific schedule.
        """
        async with self.bot.connection as connection, await connection.cursor() as cursor:
            cursor: Cursor
            await cursor.execute(SQL_FETCH_ALL)
            checks = await cursor.fetchall()
            await connection.commit()

        for entry in checks:
            identifier, mod_type, mod_slug, guild_id, channel_id, last_comment = entry

            url = f"https://www.gta5-mods.com/{mod_type}/{mod_slug}"
            channel: discord.TextChannel = self.bot.get_channel(channel_id)

            if channel is None:
                continue

            self.driver.get(url)

            try:
                message = self.driver.find_element(By.XPATH, XPATH_ERROR)

                if message.text == "The page you were looking for doesn't exist.":
                    continue
            except NoSuchElementException:
                pass

            mod_name = self.driver.find_element(By.XPATH, XPATH_MOD_TITLE).text
            elements = self.driver.find_elements(By.XPATH, XPATH_COMMENTS)

            if not elements:
                continue

            if last_comment == 0:
                element = elements[-1]
                comment_id = int(element.get_attribute("data-comment-id"))
                await _send_message_to(channel, element, mod_name, url)
                await self._update(identifier, comment_id)
                continue

            send = False

            for element in elements:
                comment_id = int(element.get_attribute("data-comment-id"))

                if last_comment == comment_id:
                    send = True
                    continue

                if send:
                    await _send_message_to(channel, element, mod_name, url)
                    await self._update(identifier, comment_id)

    @discord.Cog.listener()
    async def on_ready(self) -> None:
        """
        Function triggered when the bot is ready.
        """
        if self.bot.is_pool_available:
            async with self.bot.connection as connection, await connection.cursor() as cursor:
                cursor: Cursor
                await cursor.execute(SQL_CREATE)
                await connection.commit()

            self.check_for_comments.start()

    @discord.slash_command(name_localizations=la("MODCOMMENTS_COMMAND_ADDMOD_NAME"),
                           description=d("MODCOMMENTS_COMMAND_ADDMOD_DESC"),
                           description_localizations=la("MODCOMMENTS_COMMAND_ADDMOD_DESC"),
                           default_member_permissions=PERMISSIONS)
    @discord.option("url", type=discord.SlashCommandOptionType.string)
    async def addmod(self, ctx: discord.ApplicationContext, url: str) -> None:
        """
        Command used to add mod comments to the channel.
        """
        match = RE_LINK.fullmatch(url)

        if match is None:
            await ctx.respond(l("MODCOMMENTS_COMMAND_ADDMOD_INVALID", ctx.locale))
            return

        mod_type, mod_id = match.groups()

        async with self.bot.connection as connection, await connection.cursor() as cursor:
            cursor: Cursor
            await cursor.execute(SQL_FETCH_ONE, (mod_type, mod_id, ctx.guild.id))
            found = await cursor.fetchone()

            if found:
                await ctx.respond(l("MODCOMMENTS_COMMAND_ADDMOD_EXISTS", ctx.locale, found[0]))
                return

        async with self.bot.connection as connection, await connection.cursor() as cursor:
            cursor: Cursor
            await cursor.execute(SQL_INSERT, (mod_type, mod_id, ctx.guild.id, ctx.channel.id))
            await connection.commit()
            last = cursor.lastrowid

        await ctx.respond(l("MODCOMMENTS_COMMAND_ADDMOD_DONE", ctx.locale, mod_type, mod_id, last))

    @discord.slash_command(name_localizations=la("MODCOMMENTS_COMMAND_LISTMODS_NAME"),
                           description=d("MODCOMMENTS_COMMAND_LISTMODS_DESC"),
                           description_localizations=la("MODCOMMENTS_COMMAND_LISTMODS_DESC"),
                           default_member_permissions=PERMISSIONS)
    async def listmods(self, ctx: discord.ApplicationContext) -> None:
        """
        Command that lists the registered mods.
        """
        async with self.bot.connection as connection, await connection.cursor() as cursor:
            cursor: Cursor
            await cursor.execute(SQL_FETCH_GUILD, ctx.guild.id)
            checks = await cursor.fetchall()

        if not checks:
            await ctx.respond(l("MODCOMMENTS_COMMAND_LISTMODS_NONE", ctx.locale))
            return

        desc = "\n".join(f"{x[0]}: https://www.gta5-mods.com/{x[1]}/{x[2]} @ <#{x[3]}>" for x in checks)

        embed = discord.Embed(color=COLOR, description=desc)
        await ctx.respond(embed=embed)
