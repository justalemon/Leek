"""
Cog for parsing comments from 5mods mod pages and sending them to channels.
"""

import os

from discord import Cog, ApplicationContext
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
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
            raise ValueError(f"Unrecognized driver: {desired_driver}")

        self.driver.get("https://www.gta5-mods.com")

        self.bot: LeekBot = bot

    async def cog_before_invoke(self, ctx: ApplicationContext) -> None:  # noqa: ARG002
        """
        Checks whether the database is available before executing a command.
        """
        if not self.bot.is_pool_available:
            raise DatabaseRequiredError(self)
