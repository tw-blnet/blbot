import logging
import os
import random
import string

import discord
from discord.ext import commands
import pymysql


logging.basicConfig(level=logging.WARNING)


connection = pymysql.connect(host=os.getenv("SQL_HOST", "localhost"),
                             port=int(os.getenv("SQL_PORT", 3306)),
                             user=os.getenv("SQL_USER", "root"),
                             password=os.getenv("SQL_PASSWORD", ""),
                             db=os.getenv("SQL_DB"),
                             charset="utf8mb4",
                             cursorclass=pymysql.cursors.DictCursor,
                             autocommit=True)


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
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, username FROM record_users WHERE discord_id=%s", (ctx.author.id,))
        linked_account = cursor.fetchone()

    if linked_account is not None:
        await ctx.send(f"Your Discord account is already linked to in-game account **{linked_account['username']}** (id #{linked_account['id']}).")
        return

    with connection.cursor() as cursor:
        cursor.execute("SELECT id, username, discord_id FROM record_users WHERE discord_link_code=%s AND discord_link_issued>addtime(NOW(), '-00:05:00')", (code,))
        target_account = cursor.fetchone()

    if target_account is None:
        await ctx.send("Invalid or expired code.")
        return

    if target_account["discord_id"] is not None:
        await ctx.send("Target account is already linked.")
        return

    with connection.cursor() as cursor:
        cursor.execute("UPDATE record_users SET discord_id=%s, discord_link_code=NULL, discord_link_issued=NULL WHERE id=%s", (ctx.author.id, target_account["id"]))
    await ctx.send(f"You have successfully linked this Discord account to **{target_account['username']}** (id #{target_account['id']})")


@bot.command(
    help="checks if this Discord account is linked to a in-game account",
    ignore_extra=False,
)
async def check(ctx):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, username FROM record_users WHERE discord_id=%s", (ctx.author.id,))
        result = cursor.fetchone()

    if result is None:
        await ctx.send("No linked in-game account.")
        return

    await ctx.send(f"Linked in-game account: **{result['username']}** (id #{result['id']}).")


@bot.command(
    help="resets password for your linked in-game account",
    ignore_extra=False,
)
async def reset(ctx):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, username FROM record_users WHERE discord_id=%s", (ctx.author.id,))
        target_account = cursor.fetchone()

    if target_account is None:
        await ctx.send("No linked in-game account.")
        return

    new_password = "".join([random.choice(string.digits + string.ascii_letters) for i in range(8)])

    with connection.cursor() as cursor:
        cursor.execute("UPDATE record_users SET password=SHA2(%s, 256) WHERE id=%s", (new_password, target_account["id"]))
    await ctx.send(f"You have successfully reset password for **{target_account['username']}** (id #{target_account['id']}). Your new password: ||{new_password}||. You should change it after next login.")


def main():
    bot.run(getToken())
