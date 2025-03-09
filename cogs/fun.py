from http import server
import discord
from discord.ext import commands, tasks
import random
import func
import asyncio
import server_config


class ReactionBot(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "Reaction Commands"
        self.emoji = "👌"
        self.reactdata: list[bool] = {}
        
    async def on_load(self):
        for i in self.bot.guilds:
            await self.load_react_data_from_persistent(i.id)
        
    async def load_react_data_from_persistent(self, guild_id: int):
        reaction = (
            await server_config.get_server_config(guild_id)
        ).get("reaction_toggle")
        if reaction is None:
            print(
                f"Voice generator channel not found for guild {guild_id}. Caching as None."
            )
        self.reactdata[guild_id] = reaction

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if self.reactdata.get(message.guild.id, True):
            if "fr" in message.content:
                await message.add_reaction("🇫🇷")
            if message.content == "ts pmo":
                await message.add_reaction("💔")
            if "🗿" in message.content:
                await message.add_reaction("🗿")
            if "ok" in message.content:
                await message.add_reaction("👍")
            if "good boy" == message.content:
                await message.add_reaction("😊")
            if "this" == message.content:
                # check if the message is a reply and if so react to the original message
                if message.reference and message.reference.resolved:
                    await message.reference.resolved.add_reaction(
                        discord.PartialEmoji(name="this", id=1346958257033445387)
                    )
                await message.delete()

    @commands.has_guild_permissions(manage_guild=True)
    @commands.hybrid_command("reacttoggle")
    async def toggle(self, ctx: commands.Context):
        """Toggle reactions on messages"""
        self.reactdata[ctx.guild.id] = not self.reactdata[ctx.guild.id]
        await server_config.set_server_reaction_toggle(ctx.guild.id,int(self.reactdata[ctx.guild.id]))
        await ctx.send(
            "Reactions are now "
            + ("enabled." if self.reactdata[ctx.guild.id] else "disabled.")
        )


class StatusChanger(commands.Cog):
    def __init__(self, bot):
        self.description = "Status Changer"
        self.emoji = "🤔"
        self.bot: commands.Bot = bot

        self.statuses = [
            discord.Activity(name="you", type=discord.ActivityType.watching),
            discord.Activity(name="with you", type=discord.ActivityType.playing),
            discord.Activity(
                name="to your every word", type=discord.ActivityType.listening
            ),
            discord.CustomActivity("Sending memes to bro"),
            discord.CustomActivity("Being a good boy"),
            discord.CustomActivity("Feeding the AI overlords"),
            discord.CustomActivity("Bunnyhopping around the server"),
            discord.CustomActivity("Inspecting the default knife!"),
            discord.CustomActivity("Clutching a 1v5"),
            discord.CustomActivity("ts pmo", emoji="💔"),
            discord.CustomActivity("Playing CS:GO"),
            discord.CustomActivity("im bored hmu"),
            discord.CustomActivity("gonna hop in the shower later, wanna join?"),
            discord.CustomActivity("jorking it"),
        ]
        self.visibility = [
            discord.Status.dnd,
            discord.Status.idle,
            discord.Status.online,
        ]

    async def on_load(self):
        await self.change_status.start()

    @commands.has_guild_permissions(manage_guild=True)
    @commands.hybrid_command("statustoggle")
    async def toggle(self, ctx):
        """Toggle the status changer"""
        if self.change_status.is_running():
            await self.change_status.stop()
            await ctx.send("Status changer stopped.")
            self.bot.change_presence(status=discord.Status.online, activity=None)
        else:
            await self.change_status.start()
            await ctx.send("Status changer started.")

    @tasks.loop(minutes=1)  # Changed to minutes for cleaner syntax
    async def change_status(self):
        try:
            await self.bot.change_presence(
                activity=random.choice(self.statuses),
                status=random.choice(self.visibility),
            )
        except Exception as e:
            print(f"Error changing status: {str(e)}")


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "Game Commands"
        self.emoji = "🎮"

    @commands.hybrid_command(name="minesweeper", usage="size bombs")
    async def minesweeper(self, ctx, size: int = 9, bombs: int = 10, seed: int = None):
        """Simple Minesweeper game"""

        # Generate grid with safe start
        if seed is None:
            seed = random.randint(0, 1000000000)
        random.seed(seed)
        cx, cy = random.randint(0, size - 1), random.randint(0, size - 1)
        grid = [[0] * size for _ in range(size)]
        reserved = {
            (cx + dx, cy + dy)
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if 0 <= cx + dx < size and 0 <= cy + dy < size
        }
        available = [
            (x, y) for x in range(size) for y in range(size) if (x, y) not in reserved
        ]

        # Place bombs
        bombs = min(bombs, len(available))
        for x, y in random.sample(available, bombs):
            grid[y][x] = -1

        # Calculate numbers
        for y in range(size):
            for x in range(size):
                if grid[y][x] != -1:
                    grid[y][x] = sum(
                        grid[y + dy][x + dx] == -1
                        for dx in (-1, 0, 1)
                        for dy in (-1, 0, 1)
                        if 0 <= x + dx < size and 0 <= y + dy < size
                    )

        # Build board with revealed start
        emoji = {
            -2: "⬛",
            -1: "||💥||",
            0: "||⬛||",
            1: "||1️⃣||",
            2: "||2️⃣||",
            3: "||3️⃣||",
            4: "||4️⃣||",
            5: "||5️⃣||",
            6: "||6️⃣||",
            7: "||7️⃣||",
            8: "||8️⃣||",
            9: "||9️⃣||",
        }
        grid[cy][cx] = -2  # Reveal safe spot
        board = "\n".join(" ".join(emoji[n] for n in row) for row in grid)
        board = board.split("\n")
        # await ctx.send(content=f"Minesweeper ({size}x{size}) ({bombs} bombs):\n{board[0]}")
        # for i in range(1, size):
        #    await ctx.send(f"{board[i]}")
        emb = (
            func.Embed()
            .title("Minesweeper")
            .footer(f"{size}↔️ {bombs}💣")
            .description(f"{"\n".join(board)}")
        )
        await ctx.send(embed=emb.embed)


async def setup(bot: commands.Bot):
    react = ReactionBot(bot)
    await bot.add_cog(react)
    await react.on_load()
    
    await bot.add_cog(Games(bot))
    
    stat = StatusChanger(bot)
    await bot.add_cog(stat)
    await stat.on_load()

