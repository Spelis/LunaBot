import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
import asyncio, func
import traceback, datetime

load_dotenv()
TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("TOKEN environment variable is not set.")
PREFIX = "!" if os.getenv("PREFIX") is None else os.getenv("PREFIX")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
bot = commands.Bot(PREFIX, intents=intents, help_command=None)
bot.uptime = datetime.datetime.now()


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    
    # Get the deepest exception by walking through the __cause__ chain
    original_error = error
    while hasattr(original_error, '__cause__') and original_error.__cause__ is not None:
        original_error = original_error.__cause__
    
    error_traceback = traceback.extract_tb(original_error.__traceback__)[-1]
    filename = error_traceback.filename
    line_number = error_traceback.lineno
    line = error_traceback.line
    
    traceback.print_exception(type(error), error, error.__traceback__)
    await ctx.send(
        embed=func.Embed()
        .title("Error")
        .description(f"**Error:** {original_error}\n**File:** {filename}\n**Line {line_number}:** `{line}`")
        .color(0xf38ba8)
        .embed,
        ephemeral=True,
    )

PICKY = False # change to true if you want to load only specific extensions
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
        except Exception as e:
            if DRY_RUN:
                traceback.print_exception(type(e), e, e.__traceback__)
            print(f"Failed to load extension {extension}: {e}")


asyncio.run(load_extensions())
if DRY_RUN:
    print("Dry run complete")
    exit(0)
bot.run(TOKEN)
