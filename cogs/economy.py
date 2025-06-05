import datetime
import random

import discord
from discord import app_commands
from discord.ext import commands

import conf
import db_new
import func
from logs import Log


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.description = "Game Commands"
        self.emoji = "🎮"

    @commands.hybrid_group("star")
    async def starbits(self, ctx):
        """Starbits"""
        if ctx.invoked_subcommand is None:
            await self.starbalance(ctx)

    @starbits.command("devset")
    @func.is_developer()
    async def starset(self, ctx, user: discord.User, amount: int):
        await conf.set_starbits(user.id, amount)

    @starbits.command("claim")
    async def starcollect(self, ctx):
        """Claim your daily starbits"""
        ts = (await conf.get_user_config(ctx.author.id))["StarbitsNextCollect"]
        if int(ts) > datetime.datetime.now().timestamp():
            await ctx.send(
                f"You have already claimed your daily starbits! You can claim again <t:{round(ts)}:R>"
            )
            Log["fun"].warning(
                f"User {ctx.author.name} tried to collect starbits before time"
            )
            return
        amount = random.randint(1, 10)
        boosted = False
        if random.randint(0, 100) in random.choices(range(100), k=10):
            amount *= 2
            boosted = True

        await conf.add_starbits(ctx.author.id, amount)
        await conf.set_starbit_collection(
            ctx.author.id,
            round((datetime.datetime.now() + datetime.timedelta(days=1)).timestamp()),
        )

        next = datetime.datetime.now()
        next += datetime.timedelta(days=1)

        if boosted:
            await ctx.send(
                f"✨ Claimed boosted {amount} {discord.PartialEmoji(name="starbit",id=1349479957868318810)} starbits ✨\nYou can claim again <t:{round(next.timestamp())}:R>"
            )
        else:
            await ctx.send(
                f"Claimed {amount} {discord.PartialEmoji(name="starbit",id=1349479957868318810)} starbits\nYou can claim again <t:{round(next.timestamp())}:R>"
            )
        Log["fun"].info(
            f"User {ctx.author.id} successfully collected {amount} starbits"
        )

    @starbits.command("gamble")
    async def stargamble(self, ctx, amount: int):
        bal = (await conf.get_user_config(ctx.author.id))["Starbits"]
        if amount > bal:
            await ctx.send(f"Insufficient funds. you have {bal} starbits.")
            return
        if amount < 0:
            await ctx.send(f"Can't gamble negative funds!")
            return
        await conf.add_starbits(ctx.author.id, -amount)  # withdraw funds
        r = random.randint(1, 100)
        if r < 5:
            await ctx.send(f"JACKPOT! 10x ({amount*10})")
            await conf.add_starbits(ctx.author.id, amount * 10)
        elif r < 20:
            await ctx.send(f"Big Win! 3x ({amount*3})")
            await conf.add_starbits(ctx.author.id, amount * 3)
        elif r < 40:
            await ctx.send(f"Small Win. 1.5x ({round(amount*1.5)})")
            await conf.add_starbits(ctx.author.id, round(amount * 1.5))
        elif r < 70:
            await ctx.send(f"Loss! -100% ({amount*-1})")
            await conf.add_starbits(ctx.author.id, 0)
        elif r < 100:
            await ctx.send(f"Critical Loss! -125% ({round(amount*-1.25)})")
            await conf.add_starbits(ctx.author.id, round(amount * -0.25))

    @starbits.command("balance")
    async def starbalance(self, ctx, user: discord.Member = None):
        """Check your starbits balance"""
        if user is None:
            user = ctx.author
            t = "You have"
        else:
            t = f"{user.mention} has"
        amount = (await conf.get_user_config(user.id))["Starbits"]
        await ctx.send(
            f"{t} {amount} {discord.PartialEmoji(name="starbit",id=1349479957868318810)} starbits"
        )

    @starbits.command("top")
    async def starbaltop(self, ctx, reach: str = "global"):
        """Check the top 10 starbit holders ['global' or 'server']"""
        if reach == "global":
            title = "Global"
            async with db_new.get_session() as session:
                members = await db_new.get_all_user_ids(session)
            members = list(map(lambda member_id: ctx.bot.get_user(member_id), members))
        else:
            title = "Server"
            members = ctx.guild.members
        nm = {}
        for i in members:
            nm[i.name] = (await conf.get_user_config(i.id))["Starbits"]
        nm = dict(sorted(nm.items(), key=lambda x: x[1], reverse=True))
        emb = func.Embed().title(f"Starbits Leaderboard: (Top 10 {title})")
        for i in range(min(10, len(nm))):
            emb.section(
                f"{i+1}. {':crown: ' if i == 0 else ''}{list(nm.keys())[i]}",
                f"{discord.PartialEmoji(name="starbit",id=1349479957868318810)} {list(nm.values())[i]}",
            )
        await ctx.send(embed=emb.embed)


async def setup(bot):
    bot.add_cog(Economy(bot))
