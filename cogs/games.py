import datetime
import random

import discord
from discord import app_commands
from discord.ext import commands

import conf
import db_new
import func
from logs import Log


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

    @commands.command(name="dice", usage="*XdY")
    async def dice(self, ctx, *, s: str):
        """Roll one or more die with customizable scale (i.e: d20, 3d4)"""

        def iddice(self, d):
            s = d.split("d")
            if s[0] == "":
                s[0] = "1"
            if s[1] == "":
                s[1] = "6"
            s[0] = int(s[0])
            s[1] = int(s[1])
            r = 0
            sm = []
            for i in range(s[0]):
                i = random.randint(1, s[1])
                r += i
                sm.append(str(i))
            sm = "+".join(sm)
            return f"{s[0]}d{s[1]}", r, sm

        emb = func.Embed().title("Dice Roll")
        s = s.split(" ")
        for i in range(len(s)):
            d = iddice(self, s[i])
            s[i] = f"{d[0]} #{i}: {d[1]} ({d[2]})"
            emb.section(f"Dice #{i} ({d[0]})", f"```\n🎲 {d[1]}\n🟰 ({d[2]})```")
        await ctx.send(embed=emb.embed)


async def setup(bot):
    await bot.add_cog(Games(bot))
