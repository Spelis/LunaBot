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

load_dotenv()

TOKEN: str | None = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("TOKEN environment variable is not set.")
PREFIX: str = os.getenv("PREFIX", "!")
LOGGER_DEBUG: bool = os.getenv("LOGGER_DEBUG", "false").lower() == "true"
USE_TEX = os.getenv("USETEX", os.getenv("USE_TEX", "false")).lower() == "true"

# This was originally 1 but I changed it to 5 just to be safe with rate limiting - Script
STATUS_UPDATE_INTERVAL_MINUTES: int = 5

RANDOM_ASS_BLUE = 0x89B4FA
RANDOM_AHH_PINK = 0xF38BA8

intents: discord.Intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True


class PresenceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_status = 0

    async def cog_load(self):
        Log["presence"].info("Presence cog loaded. Starting presence update task.")
        self.update_presence_task.start()

    async def cog_unload(self):
        try:
            self.update_presence_task.stop()
            Log["presence"].info(
                "Presence cog unloaded. Stopping presence update task."
            )
        except Exception as e:
            Log["presence"].error(
                "Failed to stop presence update task. (Error propagated)", exc_info=e
            )
            raise e

    @tasks.loop(minutes=STATUS_UPDATE_INTERVAL_MINUTES)
    async def update_presence_task(self):
        random_command = random.choice(list(self.bot.commands)).qualified_name
        statuses = [
            discord.CustomActivity(
                f"Online for {str(datetime.datetime.now() - self.bot.uptime)} | /{random_command}"
            ),
            discord.Activity(
                type=discord.ActivityType.watching,
                name=f"over {len(self.bot.users)} Users | /{random_command}",
            ),
            discord.CustomActivity(
                f"{len(self.bot.guilds)} Servers! | /{random_command}"
            ),
            discord.CustomActivity(
                f"{len(self.bot.commands)} Commands! | /{random_command}"
            ),
        ]
        await self.bot.change_presence(activity=statuses[self.current_status])
        Log["presence"].info(f'Presence updated to "{statuses[self.current_status]}"')
        self.current_status += 1
        self.current_status %= len(statuses)


# pyright keeps cussing me out about the batsh- insane way that
# the custom attributes were introduced via, so I made a class.
class LunaBot(commands.AutoShardedBot):
    uptime: datetime.datetime
    use_tex: bool

    def __init__(self, *args, use_tex: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.uptime = datetime.datetime.now()
        self.use_tex = use_tex

    # I'd consider moving this task into a cog

    async def setup_hook(self) -> None:
        await load_initial_extensions()
        Log["bootstrap"].info("Loaded extensions, check errors above (if any)")

    async def on_ready(self):
        Log["bootstrap"].info(f"Successfully logged in as {self.user}")

    async def on_command_error(self, ctx, error):
        traceback.print_exception(type(error), error, error.__traceback__)
        if isinstance(error, func.NotDev):
            await ctx.send(
                embed=func.Embed()
                .title("Error")
                .description("This command is only available to developers.")
                .color(RANDOM_AHH_PINK)
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
                .color(RANDOM_AHH_PINK)
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
                .color(RANDOM_AHH_PINK)
                .embed,
                ephemeral=True,
            )
            return

        # Get the deepest exception by walking through the __cause__ chain
        original_error = error
        while (
            hasattr(original_error, "__cause__")
            and original_error.__cause__ is not None
        ):
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
            .color(RANDOM_AHH_PINK)
            .embed,
            ephemeral=True,
        )

    # -- Temporary aliases for backwards compatibility while refactoring --

    @property
    def usetex(self):
        return self.use_tex

    @usetex.setter
    def usetex(self, value: bool):
        self.use_tex = value


bot = LunaBot(PREFIX, usetex=USE_TEX, intents=intents, help_command=None)
colorama.deinit()  # allow colors for command outputs like in !gitpull

PICKY = os.getenv(
    "PICKY", default=False
)  # change to true if you want to load only specific extensions
if PICKY:
    initial_extensions = ["plug", "fun", "utils", "welcome", "voice"]
else:
    initial_extensions = list(
        map(lambda x: x[:-3], filter(lambda x: x.endswith(".py"), os.listdir("./cogs")))
    )


async def load_initial_extensions():
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
    embed.color = RANDOM_ASS_BLUE
    await ctx.send(embed=embed)


IMAGE_PATH = "image/"
IMAGE_TEMP_PATH = IMAGE_PATH + "temp/"

if not os.path.exists(IMAGE_TEMP_PATH):
    os.makedirs(IMAGE_TEMP_PATH)

print(
    "🍻 Hello World!\nYou are running a development version of Luna.\nExpect shit to break.\n- Script (unpaid intern)"
)

func.setbot(bot)
bot.run(TOKEN)
