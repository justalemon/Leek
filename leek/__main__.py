import logging
import os

from dotenv import load_dotenv

from .bot import LeekBot

LOGGER = logging.getLogger("leek")


def main():
    logging.basicConfig(level=logging.INFO)

    load_dotenv()

    bot = LeekBot()
    bot.run(os.environ["DISCORD_TOKEN"])


if __name__ == "__main__":
    main()
