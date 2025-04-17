import datetime
import os
import random
import traceback
from importlib import reload

import colorama
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

import conf
import db_new
import func
import logs
from logs import Log

# environment stuff
load_dotenv()
TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("TOKEN environment variable is not set.")
PREFIX = "!" if os.getenv("PREFIX") is None else os.getenv("PREFIX")
LOGGER_DEBUG = os.getenv("LOGGER_DEBUG", "false").lower() == "true"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
bot = commands.AutoShardedBot(PREFIX, intents=intents, help_command=None)
bot.uptime = datetime.datetime.now()
bot.curstat = 0
bot.usetex = os.getenv("USETEX", "false").lower() == "true"
colorama.deinit()  # allow colors for command outputs like in !gitpull


@bot.event
async def on_ready():
    Log["bootstrap"].info(f"Successfully logged in as {bot.user}")
    await load_extensions()
    Log["bootstrap"].info("Loaded extensions, check errors above (if any)")
    if (
        not update_presence.is_running()
    ):  # sometimes the bot restarts and runs the on_ready function.
        update_presence.start()
    Log["bootstrap"].info("Presence updater started")


@tasks.loop(minutes=1)
async def update_presence():
    randcommand = random.choice(list(bot.commands)).qualified_name
    curstat = [
        discord.CustomActivity(
            f"Online for {str(datetime.datetime.now() - bot.uptime)} | /{randcommand}"
        ),
        discord.Activity(
            type=discord.ActivityType.watching,
            name=f"over {len(bot.users)} Users | /{randcommand}",
        ),
        discord.CustomActivity(f"{len(bot.guilds)} Servers! | /{randcommand}"),
        discord.CustomActivity(f"{len(bot.commands)} Commands! | /{randcommand}"),
    ]
    await bot.change_presence(activity=curstat[bot.curstat])
    Log["presence"].info(f'Presence updated to "{curstat[bot.curstat]}"')
    bot.curstat += 1
    bot.curstat %= len(curstat)


@bot.event
async def on_command_error(ctx, error):
    traceback.print_exception(type(error), error, error.__traceback__)
    if isinstance(error, func.NotDev):
        await ctx.send(
            embed=func.Embed()
            .title("Error")
            .description("This command is only available to developers.")
            .color(0xF38BA8)
            .embed,
            ephemeral=True,
        )
        return
    if isinstance(error, commands.CommandNotFound):
        # was gonna add this, but ngl it kinda sucks if you have multiple bots with the same prefix in your server.
        # await ctx.invoke(bot.get_command("help"), args="")
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            embed=func.Embed()
            .title("Error")
            .description("You do not have permission to use this command.")
            .color(0xF38BA8)
            .embed,
            ephemeral=True,
        )
        return
    if isinstance(error, commands.CommandOnCooldown):
        sec = error.retry_after
        date = datetime.datetime.now() + datetime.timedelta(seconds=sec)
        await ctx.send(
            embed=func.Embed()
            .title("Error")
            .description(
                f"This command is on cooldown. Please try again <t:{round(date.timestamp())}:R>"
            )
            .color(0xF38BA8)
            .embed,
            ephemeral=True,
        )
        return

    # Get the deepest exception by walking through the __cause__ chain
    original_error = error
    while hasattr(original_error, "__cause__") and original_error.__cause__ is not None:
        original_error = original_error.__cause__

    error_traceback = traceback.extract_tb(original_error.__traceback__)[-1]
    filename = error_traceback.filename
    line_number = error_traceback.lineno
    line = error_traceback.line

    await ctx.send(
        embed=func.Embed()
        .title("Error")
        .description(
            f"**Error:** ```{original_error}```\n**File:** {filename}\n**Line {line_number}:** `{line}`"
        )
        .color(0xF38BA8)
        .embed,
        ephemeral=True,
    )


PICKY = os.getenv(
    "PICKY", default=False
)  # change to true if you want to load only specific extensions
if PICKY:
    initial_extensions = ["plug", "fun", "utils", "welcome", "voice"]
else:
    initial_extensions = list(map(lambda x: x[:-3], os.listdir("./cogs")))
    if "__pycach" in initial_extensions:
        initial_extensions.remove("__pycach")  # remove __pycache__


async def load_extensions():
    for extension in initial_extensions:
        try:
            await bot.load_extension("cogs." + extension)
            Log["bootstrap"].info(f'Successfully loaded extension "{extension}"')
        except Exception:
            traceback.print_exc(3)
            Log["bootstrap"].error(
                f'Failed to load extension "{extension}". Check error above'
            )


@bot.hybrid_command("rfile")  # here this command has access to everything
@func.is_developer()
async def reloadfile(ctx, file):
    """Reloads a file (Developer only)"""
    reload(globals()[file])
    embed = discord.Embed()  # use normal embeds, this command breaks stuff otherwise
    embed.title = "Reloaded File"
    embed.description = f"{file} has been successfully reloaded."
    embed.color = 0x89B4FA
    await ctx.send(embed=embed)


IMAGE_PATH = "image/"
IMAGE_TEMP_PATH = IMAGE_PATH + "temp/"

if not os.path.exists(IMAGE_TEMP_PATH):
    os.makedirs(IMAGE_TEMP_PATH)

func.setbot(bot)
bot.run(TOKEN)
