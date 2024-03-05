"""
Tools for helping with the modding of RAGE Games.
"""

import logging
import string

from aiohttp import ClientResponseError
from discord import ApplicationContext, AutocompleteContext, Cog, Embed, Option, slash_command

from leek import LeekBot, get_default, get_localizations

LOGGER = logging.getLogger("leek_modding")
NATIVE_LINKS = {
    "gtav": "https://raw.githubusercontent.com/alloc8or/gta5-nativedb-data/master/natives.json",
    "rdr3": "https://raw.githubusercontent.com/alloc8or/rdr3-nativedb-data/master/natives.json",
    "fivem": "https://runtime.fivem.net/doc/natives_cfx.json"
}
NATIVES = {}
CACHE = []


def format_lua_name(name: str) -> str:
    """
    Formats the name of a native to it's Lua compatible name.
    """
    return string.capwords(name.lower().replace("0x", "N_0x").replace("_", " ")).replace(" ", "")


def format_params(params: dict) -> str:
    """
    Formats the parameters as a string.
    """
    if params is None:
        return ""

    formatted = "\n    "

    for param in params:
        p_type = param["type"]
        p_name = param["name"]
        description = param.get("description", None)

        formatted += "`{0}: {1}`".format(p_name, p_type)

        if description:
            formatted += " {0}\n".format(description)
        else:
            formatted += "\n"

    return formatted


def find_native(name: str, game: str) -> dict | None:
    """
    Finds a native by its partial name.
    """
    natives = NATIVES.get(game)

    if natives is None:
        return None

    return next((x for x in natives if name in (x["hash"], x["name"])), None)


async def get_natives(ctx: AutocompleteContext) -> list[str]:
    """
    Gets the native that match the partial lookup.
    """
    query = ctx.value.upper()
    return [x for x in CACHE if query in x]


async def get_games(ctx: AutocompleteContext) -> list[str]:  # noqa: ARG001
    """
    Gets the list of available games.
    """
    return list(NATIVES.keys())


class Rage(Cog):
    """
    Tools for Rockstar Advanced Game Engine modders.
    """
    def __init__(self, bot: LeekBot):
        """
        Creates a new RAGE Cog.
        """
        self.bot: LeekBot = bot

    @Cog.listener()
    async def on_connect(self) -> None:
        """
        Downloads the list of natives when connecting to Discord.
        """
        for game, url in NATIVE_LINKS.items():
            try:
                async with await self.bot.get(url) as resp:
                    resp.raise_for_status()
                    json: dict[str, dict[str, dict[str, str]]] = await resp.json(content_type=None)
                    ready = []

                    CACHE.clear()

                    for namespace, natives in json.items():
                        for n_hash, n_data in natives.items():
                            name = n_data["name"]
                            native = {
                                "namespace": namespace,
                                "hash": n_hash,
                                "lua": format_lua_name(name),
                                **n_data
                            }

                            if name not in CACHE:
                                CACHE.append(name)
                            if n_hash not in CACHE:
                                CACHE.append(n_hash)

                            if n_hash in NATIVES:
                                LOGGER.warning("Found Duplicated Native: %s/%s", n_hash, name)

                            ready.append(native)

                    NATIVES[game] = ready

                CACHE.sort(reverse=True)
            except ClientResponseError as e:
                LOGGER.exception("Can't request %s: Code %s", url, e.status)
            except BaseException:
                LOGGER.exception("Unable to get %s natives from %s", game, url)

        LOGGER.info("Finished fetching the natives")

    @slash_command(name_localizations=get_localizations("MODDING_COMMAND_NATIVE_NAME"),
                   description=get_default("MODDING_COMMAND_NATIVE_DESC"),
                   description_localizations=get_localizations("MODDING_COMMAND_NATIVE_DESC"))
    async def native(self, ctx: ApplicationContext, name: Option(str, "The name to search", autocomplete=get_natives),
                     game: Option(str, "The game for this native", default="gtav",
                                  autocomplete=get_games)) -> None:
        """
        Searches for the documentation of a native.
        """
        found = find_native(name, game)

        if found is None:
            await ctx.respond("The native was not found!", ephemeral=True)
            return

        params = format_params(found["params"])

        embed = Embed()
        embed.title = found["name"]
        embed.description = "**Hash**: {0}\n**Lua Name**: {1}\n**Parameters**: {2}".format(found["hash"],
                                                                                           found["lua"],
                                                                                           params)

        backup = embed.description
        comment = found.get("comment", None) or found.get("description")

        if comment:
            embed.description += "\n**Description**: {0}".format(comment)

            if len(embed) > 2000:
                embed.description = backup

        await ctx.respond(embed=embed)
