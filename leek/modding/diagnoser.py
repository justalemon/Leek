import re

from discord import Cog, ApplicationContext, message_command, Message, Embed
from leek import LeekBot, get_default


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
    "Failed to load config: System.IO.FileNotFoundException": "The configuration file for SHVDN does not exists",
    RE_INSTANCE: "Mod {0} was not instantiated by SHVDN",
    RE_DEPENDENCY: "{0} requires {1} version {2} or higher but is not installed",
    RE_ASSEMBLY: "{0} requires {1} version {2} or higher but is not installed",
    RE_CONSTRUCTOR: "Mod {0} is missing a constructor or the Attribute NoDefaultInstance",
    RE_CRASHED: "{0} crashed, contact the developer with this log file"
}
LEVELS = {
    "WARNING": "🟡",
    "ERROR": "🔴"
}
FATAL_EXCEPTION = "Caught fatal unhandled exception:"
ABORTED_SCRIPT = "Aborted script "


class Diagnoser(Cog):
    def __init__(self, bot: LeekBot):
        self.bot = bot

    @message_command(name=get_default("MODDING_MESSAGE_DIAGNOSE_NAME"))
    async def diagnose(self, ctx: ApplicationContext, message: Message):
        if not message.attachments:
            await ctx.respond("There are no log files attached to this message.")
            return

        attachment = message.attachments[0]

        if not attachment.content_type.startswith("text/plain"):
            await ctx.respond("The attachment is not a text file.")
            return

        async with await self.bot.get(attachment.url) as response:
            if not response.ok:
                await ctx.respond(f"Couldn't fetch log file: Code {response.status}")
                return

            content = await response.text()
            lines = content.splitlines()

        problems = []

        for line in lines:
            match = RE_SHVDN.search(line)

            if match is None:
                continue

            level, details = match.groups()

            if level not in LEVELS or details == FATAL_EXCEPTION or details.startswith(ABORTED_SCRIPT):
                continue

            emoji = LEVELS[level]
            matched = False

            for match, text in MATCHES.items():
                if isinstance(match, re.Pattern):
                    matches = match.match(details)

                    if matches is None:
                        continue

                    message = f"{emoji} " + text.format(*matches.groups())
                elif isinstance(match, str):
                    if not details.startswith(match):
                        continue

                    message = f"{emoji} {text}"
                else:
                    continue

                if message not in problems:
                    problems.append(message)

                matched = True
                break

            if not matched:
                problems.append(f"{emoji} Unknown ({details})")

        if not problems:
            await ctx.respond("Couldn't detect any issues with the log file.")
        else:
            embed = Embed()
            embed.title = f"Found {len(problems)} problems"
            embed.description = "\n".join(problems)
            await ctx.respond(embed=embed)
