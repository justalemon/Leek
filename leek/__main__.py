"""
Starts the Leek bot and the desired cogs.
"""

import importlib
import logging
import os
import sys
import warnings
from typing import Optional, Union

from discord import Cog, Intents
from dotenv import load_dotenv

from .bot import LeekBot

LOGGER = logging.getLogger("leek")


def _get_int_safe(key: str, default: Optional[int] = None) -> Optional[int]:
    """
    Gets an environment variable safely as an int.
    :param key: The environment variable to get.
    :param default: The default value to use, if is not present.
    :return: The variable as an integer, or None if is not valid.
    """
    try:
        return int(os.environ.get(key, default))
    except TypeError:
        return None
    except KeyError:
        return None
    except ValueError:
        LOGGER.exception("Environment variable %s is not a valid number!", key)
        return None


def _get_sql_connection() -> Optional[dict[str, Union[str, int, None]]]:
    """
    Gets the SQL Connection details from the environment variables.
    :return: The SQL Connection details as a dictionary.
    """
    config = {
        "host": os.environ.get("SQL_HOST", "127.0.0.1"),
        "port": _get_int_safe("SQL_PORT", 3306),
        "user": os.environ.get("SQL_USER", None),
        "password": os.environ.get("SQL_PASSWORD", None),
        "db": os.environ.get("SQL_DB", "leek")
    }
    return None if any(x is None for x in config.values()) else config


def main() -> None:
    """
    Starts the bot.
    """
    logging.basicConfig(level=logging.INFO)

    load_dotenv()

    if "DISCORD_TOKEN" not in os.environ:
        LOGGER.error("Discord Token is not set")
        sys.exit(2)

    debug_guilds = [int(x) for x in os.environ.get("DISCORD_GUILDS", "").split(",")]

    if debug_guilds:
        LOGGER.info("Found Guilds in debug mode: %s", debug_guilds)

    bot = LeekBot(debug=os.environ.get("DISCORD_DEBUG", "0") != "0",
                  pool_info=_get_sql_connection(),
                  intents=Intents.all(),
                  debug_guilds=debug_guilds)

    cogs_to_load = os.environ.get("DISCORD_COGS", "").split(",")

    for cog_name in cogs_to_load:
        name = cog_name.strip()

        if not name:
            continue

        split = name.split(":")

        if len(split) != 2:
            LOGGER.error("Cog name '%s' is not in the right format", name)
            continue

        try:
            imported = importlib.import_module(split[0])
        except ModuleNotFoundError:
            LOGGER.exception("Unable to import '%s' because it couldn't be found", name)
            continue

        if not hasattr(imported, split[1]):
            LOGGER.error("Unable to load '%s' from '%s' because the class does not exists", split[1], split[1])
            continue

        cog = getattr(imported, split[1])

        if not issubclass(cog, Cog):
            LOGGER.error("Class '%s' does not inherits from a Cog", name)
            continue

        try:
            bot.add_cog(cog(bot))
        except Exception:
            # We catch everything because we don't know what exception might be triggered
            LOGGER.exception("Unable to start '%s'", name)
        finally:
            LOGGER.info("Added cog %s", name)

    warnings.filterwarnings(os.environ.get("SQL_WARNINGS", "ignore"), module="aiomysql")

    bot.run(os.environ["DISCORD_TOKEN"])


if __name__ == "__main__":
    main()
