import os

from dotenv import load_dotenv

from .bot import LeekBot


def main():
    load_dotenv()

    bot = LeekBot()
    bot.run(os.environ["DISCORD_TOKEN"])


if __name__ == "__main__":
    main()
