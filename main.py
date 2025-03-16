import discord
import os
from discord.ext import commands,tasks
from dotenv import load_dotenv
import func
import traceback
import datetime
from logs import Log
from importlib import reload
import database_conf


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


@bot.event
async def on_ready():
    Log['bootstrap'].info(f"Successfully logged in as {bot.user}")
    await load_extensions()
    Log['bootstrap'].info("Loaded extensions, check errors above (if any)")
    if not update_presence.is_running(): # sometimes the bot restarts and runs the on_ready function.
        update_presence.start()
    Log['bootstrap'].info("Presence updater started")

@tasks.loop(minutes=1)
async def update_presence():
    curstat = [
        discord.CustomActivity(f"Watching over {len(bot.users)} Users | /help"),
        discord.CustomActivity(f"{len(bot.guilds)} Servers! | /help"),
        discord.CustomActivity(f"Online for {func.td_format(datetime.datetime.now() - bot.uptime)} | /help"),
    ]
    bot.curstat += 1
    bot.curstat %= len(curstat)
    await bot.change_presence(activity=curstat[bot.curstat])
    Log['presence'].info(f"Presence updated to \"{curstat[bot.curstat]}\"")

@bot.event
async def on_command_error(ctx, error):
    traceback.print_exception(type(error), error, error.__traceback__)
    if isinstance(error,func.NotDev):
        await ctx.send(
            embed=func.Embed()
            .title("Error")
            .description("This command is only available to developers.")
            .color(0xf38ba8)
            .embed,
            ephemeral=True,
        )
        return
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            embed=func.Embed()
            .title("Error")
            .description("You do not have permission to use this command.")
            .color(0xf38ba8)
            .embed,
            ephemeral=True,
        )
        return
    if isinstance(error,commands.CommandOnCooldown):
        sec = error.retry_after
        date = datetime.datetime.now() + datetime.timedelta(seconds=sec)
        await ctx.send(
            embed=func.Embed()
            .title("Error")
            .description(
                f"This command is on cooldown. Please try again <t:{round(date.timestamp())}:R>"
            )
            .color(0xf38ba8)
            .embed,
            ephemeral=True,
        )
        return
    
    # Get the deepest exception by walking through the __cause__ chain
    original_error = error
    while hasattr(original_error, '__cause__') and original_error.__cause__ is not None:
        original_error = original_error.__cause__
    
    error_traceback = traceback.extract_tb(original_error.__traceback__)[-1]
    filename = error_traceback.filename
    line_number = error_traceback.lineno
    line = error_traceback.line
    
    await ctx.send(
        embed=func.Embed()
        .title("Error")
        .description(f"**Error:** ```{original_error}```\n**File:** {filename}\n**Line {line_number}:** `{line}`")
        .color(0xf38ba8)
        .embed,
        ephemeral=True,
    )

PICKY = os.getenv("PICKY",default=False) # change to true if you want to load only specific extensions
if PICKY:
    initial_extensions = ["plug", "fun", "utils", "welcome","voice"]
else:
    initial_extensions = list(map(lambda x: x[:-3], os.listdir("./cogs")))
    if "__pycach" in initial_extensions:
        initial_extensions.remove("__pycach") # remove __pycache__


async def load_extensions():
    for extension in initial_extensions:
        try:
            await bot.load_extension("cogs." + extension)
            Log['bootstrap'].info(f"Successfully loaded extension \"{extension}\"")
        except Exception as e:
            traceback.print_exc(3)
            Log['bootstrap'].error(f"Failed to load extension \"{extension}\". Check error above")
            
@bot.hybrid_command("rfile") # here this command has access to everything
@func.is_developer()
async def reloadfile(ctx, file):
    """Reloads a file (Developer only)"""
    reload(globals()[file])
    await ctx.send(
        embed=func.Embed()
        .title("Reloaded File")
        .description(f"{file} has been successfully reloaded.")
        .color(0x89B4FA)
        .embed
    )
            
            
bot.run(TOKEN)
