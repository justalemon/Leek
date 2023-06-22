"""
Starts the Leek bot and the desired cogs.
"""

import importlib
import logging
import os
import sys
from typing import Optional

from discord import Intents, Cog
from dotenv import load_dotenv

from .bot import LeekBot

LOGGER = logging.getLogger("leek")


def _get_int_safe(key: str, default: Optional[int] = None):
    try:
        return int(os.environ.get(key, default))
    except TypeError:
        return None
    except KeyError:
        return None
    except ValueError:
        LOGGER.error(f"Environment variable {key} is not a valid number!")
        return None


def _get_sql_connection():
    config = {
        "host": os.environ.get("SQL_HOST", "127.0.0.1"),
        "port": _get_int_safe("SQL_PORT", 3306),
        "user": os.environ.get("SQL_USER", None),
        "password": os.environ.get("SQL_PASSWORD", None),
        "db": os.environ.get("SQL_DB", "leek")
    }
    return None if any(x is None for x in config.values()) else config


def main():
    """
    Starts the bot.
    """
    logging.basicConfig(level=logging.INFO)

    load_dotenv()

    if "DISCORD_TOKEN" not in os.environ:
        LOGGER.error("Discord Token is not set")
        sys.exit(2)

    bot = LeekBot(debug=os.environ.get("DISCORD_DEBUG", "0") != "0",
                  pool_info=_get_sql_connection(),
                  intents=Intents.all())

    cogs_to_load = os.environ.get("DISCORD_COGS", "").split(",")

    for name in cogs_to_load:
        name = name.strip()

        if name == "":
            continue

        split = name.split(":")

        if len(split) != 2:
            LOGGER.error(f"Cog name '{name}' is not in the right format")
            continue

        try:
            imported = importlib.import_module(split[0])
        except ModuleNotFoundError:
            LOGGER.error(f"Unable to import '{name}' because it couldn't be found")
            continue

        if not hasattr(imported, split[1]):
            LOGGER.error(f"Unable to load '{split[1]}' from '{split[1]} because the class does not exists")
            continue

        cog = getattr(imported, split[1])

        if not issubclass(cog, Cog):
            LOGGER.error(f"Class '{name}' does not inherits from a Cog")
            continue

        try:
            bot.add_cog(cog(bot))
        except Exception:
            LOGGER.exception(f"Unable to start '{name}'")
        finally:
            LOGGER.info(f"Added cog {name}")

    bot.run(os.environ["DISCORD_TOKEN"])


if __name__ == "__main__":
    main()
