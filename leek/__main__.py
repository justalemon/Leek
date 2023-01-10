import logging
import os
import sys

from discord import Intents
from dotenv import load_dotenv

from .bot import LeekBot

LOGGER = logging.getLogger("leek")


def main():
    logging.basicConfig(level=logging.INFO)

    load_dotenv()

    if "DISCORD_TOKEN" not in os.environ:
        LOGGER.error("Discord Token is not set")
        sys.exit(2)

    bot = LeekBot(intents=Intents.all())
    bot.run(os.environ["DISCORD_TOKEN"])


if __name__ == "__main__":
    main()
