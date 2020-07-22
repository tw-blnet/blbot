import logging
import os

import discord
from discord.ext import commands


logging.basicConfig(level=logging.WARNING)


def getToken():
    token = os.getenv("TOKEN")
    if token:
        return token

    with open(".token") as f:
        token = f.read().strip("\n")

    return token


class HelpCommand(commands.DefaultHelpCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_ending_note(self):
        return "Type 'help command' for more info on a command."


ACTIVITY_NAME = os.getenv("ACTIVITY")

bot = commands.Bot(
    command_prefix="",
    case_insensitive=True,
    description="I can help you manage your in-game account. With my help you can link your in-game account to this Discord account. Then you can reset your password if you forget it.",
    help_command=HelpCommand(no_category="All commands"),
    activity=discord.Game(name=ACTIVITY_NAME) if ACTIVITY_NAME is not None else None,
)


@bot.event
async def on_ready():
    bot.description = f"Hi I'm {bot.user.name}! {bot.description}"


@bot.event
async def on_command_error(ctx, error):
    if not await only_dm(ctx):
        return

    EXCEPTION_MESSAGES = {
        commands.CommandNotFound: "No such command found! Use `help` to see all available commands.",
        commands.TooManyArguments: "Too many arguments! Use `help` to see usage of all available commands.",
        commands.MissingRequiredArgument: "Missing required arguments! Use `help` to see usage of all available commands.",
        commands.BadArgument: "Wrong arguments passed! Use `help` to see usage of all available commands.",
        commands.ArgumentParsingError: "Wrong arguments passed! Use `help` to see usage of all available commands.",
    }

    for exception, message in EXCEPTION_MESSAGES.items():
        if isinstance(error, exception):
            await ctx.send(message)


@bot.check
async def only_dm(ctx):
    return ctx.channel.type == discord.ChannelType.private


@bot.command(
    help="links this Discord account to in-game account",
    ignore_extra=False,
)
async def link(ctx, code: int):
    pass


@bot.command(
    help="checks if this Discord account is linked to a in-game account",
    ignore_extra=False,
)
async def check(ctx):
    pass


@bot.command(
    help="resets password for your linked in-game account",
    ignore_extra=False,
)
async def reset(ctx):
    pass


def main():
    bot.run(getToken())
