"""
Tool used to diagnose the SHVDN Log Files.
"""

import re

from discord import ApplicationContext, Cog, Embed, Message, message_command

from leek import LeekBot, d, l

RE_SHVDN = re.compile("\\[[0-9]{2}:[0-9]{2}:[0-9]{2}] \\[(WARNING|ERROR)] (.*)")
RE_INSTANCE = re.compile("A script tried to use a custom script instance of type ([A-Za-z0-9_.]*) that was not "
                         "instantiated by ScriptHookVDotNet")
RE_DEPENDENCY = re.compile("Failed to instantiate script ([A-Za-z0-9_.]*) because constructor threw an exception: "
                           "System.IO.FileNotFoundException: .* '([A-Za-z0-9.]*), Version=([0-9.]*),")
RE_ASSEMBLY = re.compile("Failed to load assembly ([A-Za-z0-9_.]*).dll: System.IO.FileNotFoundException: "
                         "Could not load file or assembly '([A-Za-z0-9.]*), Version=([0-9.]*),")
RE_CONSTRUCTOR = re.compile("Failed to instantiate script ([A-Za-z0-9_.]*) because no public default "
                            "constructor was found")
RE_CRASHED = re.compile("The exception was thrown while executing the script ([A-Za-z0-9_.]*)")
MATCHES = {
    "Failed to load config: System.IO.FileNotFoundException": "MESSAGE_DIAGNOSE_MATCH_MISSING_CONFIG",
    RE_INSTANCE: "MESSAGE_DIAGNOSE_MATCH_INSTANCE_INVALID",
    RE_DEPENDENCY: "MESSAGE_DIAGNOSE_MATCH_DEPENDENCY_MISSING",
    RE_ASSEMBLY: "MESSAGE_DIAGNOSE_MATCH_ASSEMBLY_MISSING",
    RE_CONSTRUCTOR: "MESSAGE_DIAGNOSE_MATCH_CONSTRUCTOR_MISSING",
    RE_CRASHED: "MESSAGE_DIAGNOSE_MATCH_CRASHED",
}
LEVELS = {
    "WARNING": "🟡",
    "ERROR": "🔴"
}
FATAL_EXCEPTIONS = [
    "Caught fatal unhandled exception:",
    "Caught unhandled exception:"
]
ABORTED_SCRIPT = "Aborted script "


def get_problems(locale: str, lines: list[str]) -> list[str]:  # noqa: C901
    """
    Gets the problems in the lines of a file.
    """
    problems = []

    for line in lines:
        match = RE_SHVDN.search(line)

        if match is None:
            continue

        level, details = match.groups()

        if level not in LEVELS or details in FATAL_EXCEPTIONS or details.startswith(ABORTED_SCRIPT):
            continue

        emoji = LEVELS[level]
        matched = False

        for match, label in MATCHES.items():
            if isinstance(match, re.Pattern):
                matches = match.match(details)

                if matches is None:
                    continue

                message = f"{emoji} " + l(label, locale, *matches.groups())
            elif isinstance(match, str):
                if not details.startswith(match):
                    continue

                message = f"{emoji} " + l(label, locale)
            else:
                continue

            if message not in problems:
                problems.append(message)

            matched = True
            break

        if not matched:
            problems.append(f"{emoji} Unknown ({details})")

    return problems


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

        async with await self.bot.get(attachment.url) as response:
            if not response.ok:
                await ctx.respond(l("MESSAGE_DIAGNOSE_FAILED", ctx.locale, response.status))
                return

            content = await response.text()
            lines = content.splitlines()

        problems = get_problems(ctx.locale, lines)

        if not problems:
            await ctx.respond(l("MESSAGE_DIAGNOSE_NOTHING", ctx.locale))
        else:
            embed = Embed()
            embed.title = f"Found {len(problems)} problems"
            embed.description = "\n".join(problems)
            await ctx.respond(embed=embed)
