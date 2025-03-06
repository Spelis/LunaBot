import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
import asyncio,func
import traceback,datetime

load_dotenv()
TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("TOKEN environment variable is not set.")
PREFIX = "!" if os.getenv("PREFIX") is None else os.getenv("PREFIX")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
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
    traceback.print_exception(type(error), error, error.__traceback__)
    await ctx.send(embed=func.Embed().title("Error").description(f"An error occurred: {error}").color(0xFF0000).embed,ephemeral=True)

initial_extensions = ["plug","fun","utils","welcome"]

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
