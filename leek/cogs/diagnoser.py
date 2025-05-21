"""
Tool used to diagnose the SHVDN Log Files.
"""

import re

from discord import ApplicationContext, Cog, Embed, Message, message_command

from leek import LeekBot, d, l

RE_SHVDN = re.compile("\\[[0-9]{2}:[0-9]{2}:[0-9]{2}] \\[(WARNING|ERROR)] (.*)")
RE_LEGACY_ZERO = re.compile("Resolving API version 0.0.0 referenced in (.+\\.dll).")
RE_INSTANCE = re.compile("A script tried to use a custom script instance of type ([A-Za-z0-9_.+]*) that was not "
                         "instantiated by ScriptHookVDotNet")
RE_DEPENDENCY = re.compile("Failed to instantiate script ([A-Za-z0-9_.+]*) because constructor threw an exception: "
                           "System.IO.FileNotFoundException: .* '([A-Za-z0-9.]*), Version=([0-9.]*),")
RE_INIT_CRASH = re.compile("Failed to instantiate script ([A-Za-z0-9_.+]*) because constructor threw an exception:")
RE_ASSEMBLY = re.compile("Failed to load assembly ([A-Za-z0-9_.+]*).dll: System.IO.FileNotFoundException: "
                         "Could not load file or assembly '([A-Za-z0-9_.+]*), Version=([0-9.]*),")
RE_CONSTRUCTOR = re.compile("Failed to instantiate script ([A-Za-z0-9_.+]*) because no public default "
                            "constructor was found")
RE_CRASHED = re.compile("The exception was thrown while executing the script ([A-Za-z0-9_.]*)")
MATCHES = {
    "Failed to load config: System.IO.FileNotFoundException": "MESSAGE_DIAGNOSE_MATCH_MISSING_CONFIG",
    RE_LEGACY_ZERO: "MESSAGE_DIAGNOSE_MATCH_LEGACY_ZERO",
    RE_INSTANCE: "MESSAGE_DIAGNOSE_MATCH_INSTANCE_INVALID",
    RE_DEPENDENCY: "MESSAGE_DIAGNOSE_MATCH_DEPENDENCY_MISSING",
    RE_INIT_CRASH: "MESSAGE_DIAGNOSE_MATCH_CONSTRUCTOR_CRASH",
    RE_ASSEMBLY: "MESSAGE_DIAGNOSE_MATCH_ASSEMBLY_MISSING",
    RE_CONSTRUCTOR: "MESSAGE_DIAGNOSE_MATCH_CONSTRUCTOR_MISSING",
    RE_CRASHED: "MESSAGE_DIAGNOSE_MATCH_CRASHED",
}
VER_TWO_WARNING = "script(s) resolved to the deprecated API version 2.x (ScriptHookVDotNet2.dll)"
FATAL_EXCEPTIONS = [
    "Caught fatal unhandled exception:",
    "Caught unhandled exception:"
]
ABORTED_SCRIPT = "Aborted script "


def get_problems(locale: str, lines: list[str]) -> tuple[dict[str, int], dict[str, int]]:  # noqa: C901
    """
    Gets the problems in the lines of a file.
    """
    warnings: dict[str, int] = {}
    errors: dict[str, int] = {}

    def add_message(level: str, message: str) -> None:
        if level == "WARNING":
            msg = "🟡 " + message
            warnings[msg] = warnings.get(msg, 0) + 1
        elif level == "ERROR":
            msg = "🔴 " + message
            errors[msg] = errors.get(msg, 0) + 1

    is_processing_ver_two_warning = False

    for line in lines:
        match = RE_SHVDN.search(line)

        # deprecation warnings tend to be followed by "[DEBUG] Instantiating script"
        # this should cleanly not trigger any matches and set the variable to false

        if match is None:
            is_processing_ver_two_warning = False
            continue

        level, details = match.groups()

        if is_processing_ver_two_warning:
            add_message("WARNING", l("MESSAGE_DIAGNOSE_MATCH_LEGACY_TWO", locale, details))
            continue

        if VER_TWO_WARNING in details:
            is_processing_ver_two_warning = True
            continue

        if level not in ["WARNING", "ERROR"] or details in FATAL_EXCEPTIONS or details.startswith(ABORTED_SCRIPT):
            continue

        matched = False

        for match, label in MATCHES.items():
            if isinstance(match, re.Pattern):
                matches = match.match(details)

                if matches is None:
                    continue

                message = l(label, locale, *matches.groups())
            elif isinstance(match, str):
                if not details.startswith(match):
                    continue

                message = l(label, locale)
            else:
                continue

            add_message(level, message)

            matched = True
            break

        if not matched:
            add_message(level, l("MESSAGE_DIAGNOSE_MATCH_UNKNOWN", locale, details))

    return warnings, errors


class Diagnoser(Cog):
    """
    A Cog used to diagnose log files of ScriptHookVDotNet.
    """
    def __init__(self, bot: LeekBot):
        """
        Creates a new diagnoser.
        """
        self.bot = bot

    @message_command(name=d("MESSAGE_DIAGNOSE_NAME"))
    async def diagnose(self, ctx: ApplicationContext, message: Message) -> None:
        """
        Tries to make a partial diagnostic of a SHVDN Log File.
        """
        if not message.attachments:
            await ctx.respond(l("MESSAGE_DIAGNOSE_NOT_ATTACHED", ctx.locale))
            return

        attachment = message.attachments[0]

        if not attachment.content_type.startswith("text/plain"):
            await ctx.respond(l("MESSAGE_DIAGNOSE_NOT_VALID", ctx.locale))
            return

        await ctx.defer()

        async with await self.bot.get(attachment.url) as response:
            if not response.ok:
                await ctx.respond(l("MESSAGE_DIAGNOSE_FAILED", ctx.locale, response.status))
                return

            content = await response.text()
            lines = content.splitlines()

        warnings, errors = get_problems(ctx.locale, lines)
        embed = Embed()

        if len(warnings) == 0 and len(errors) == 0:
            embed.colour = 0x6fff00
            embed.title = l("MESSAGE_DIAGNOSE_NOTHING", ctx.locale)
            await ctx.respond(embed=embed)

        embed.colour = 0xff1100 if errors else 0xffe100
        embed.title = l("MESSAGE_DIAGNOSE_FOUND", ctx.locale, len(errors), len(warnings))

        messages = [f"{m} ({c})" for m, c in errors.items()] + [f"{m} ({c})" for m, c in warnings.items()]

        responded = False

        for msg in messages:
            d = f"{embed.description}\n" if embed.description else ""
            new = f"{d}{msg}"
            if len(new) > 4096:
                if responded:
                    await ctx.send(embed=embed)
                else:
                    await ctx.respond(embed=embed)
                    responded = True
                embed.description = msg
                embed.title = None
            else:
                embed.description = new

        if len(embed.description) > 0:
            if responded:
                await ctx.send(embed=embed)
            else:
                await ctx.respond(embed=embed)
