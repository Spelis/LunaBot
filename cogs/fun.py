from http import server
import discord
from discord.ext import commands
import random
import func
import server_config
import matplotlib.pyplot as plt


class ReactionBot(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "Reaction Commands"
        self.emoji = "👌"
        self.reactdata: list[bool] = {}
        
    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        for i in self.bot.guilds:
            await self.load_react_data_from_persistent(i.id)
        
    async def load_react_data_from_persistent(self, guild_id: int):
        reaction = (
            await server_config.get_server_config(guild_id)
        ).get("reaction_toggle")
        if reaction is None:
            print(
                f"Reaction toggle unset, defaulting to True for guild {guild_id}."
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
            if "ok" in message.content: # probably make this one use regex
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

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "Game Commands"
        self.emoji = "🎮"

    @commands.hybrid_command("latex")
    async def latex(self, ctx, latex: str=""):
        """Render LaTeX"""
        # check if the message contains an attachment (higher priority than the argument)
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            latex = await attachment.read()
            latex = latex.decode('utf-8')
        fig = plt.figure(figsize=(4, 1))
        ax = plt.axes([0, 0, 1, 1])
        ax.axis('off') # remove axes
        ax.text(0.5, 0.5, f'${latex}$', # render LaTeX
                fontsize=20, 
                ha='center', va='center')
        temp_path = 'temp.png'
        plt.savefig(temp_path) # save temporary image
        plt.close(fig)
        await ctx.send(file=discord.File(temp_path)) # Send the image

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
    await bot.add_cog(Games(bot))
    await bot.add_cog(ReactionBot(bot))
    

