"""
Cog for parsing comments from 5mods mod pages and sending them to channels.
"""

import os

from discord import Cog, ApplicationContext
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from leek import DatabaseRequiredError, LeekBot


class ModComments(Cog):
    """
    Comment parser an redirector for 5mods.
    """
    def __init__(self, bot: LeekBot):
        """
        Creates a new Cog.
        """
        desired_driver = os.environ.get("MODCOMMENTS_DRIVER", "firefox").lower()

        if desired_driver == "firefox":
            self.driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
            self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        elif desired_driver == "chrome":
        else:
            raise ValueError(f"Unrecognized driver: {desired_driver}")

        self.driver.get("https://www.gta5-mods.com")

        self.bot: LeekBot = bot

    async def cog_before_invoke(self, ctx: ApplicationContext) -> None:  # noqa: ARG002
        """
        Checks whether the database is available before executing a command.
        """
        if not self.bot.is_pool_available:
            raise DatabaseRequiredError(self)
