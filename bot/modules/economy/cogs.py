import random

import discord
from discord.ext import commands

from bot.database import get_session
from bot.luna import LunaBot

from .services import EconomyService


class Economy(commands.Cog):
    def __init__(self, bot: LunaBot) -> None:
        self.bot: LunaBot = bot

    @commands.hybrid_group("star")
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def star(self, ctx: commands.Context):
        """Economy commands"""
        if ctx.invoked_subcommand is None:
            await self.star_balance(ctx)

    @star.command("balance")
    async def star_balance(
        self, ctx: commands.Context, user: discord.Member | None = None
    ):
        """Check your starbit balance"""
        if user is None:
            user: discord.User = ctx.author
            t: str = "You have"
        else:
            t: str = f"{user.mention} has"
        async with get_session() as session:
            svc = EconomyService.from_session(session)
            usr_obj = await svc.get(user.id)
            balance = 0
            if usr_obj is not None:
                balance = usr_obj.balance
            else:
                _ = await svc.create(user.id)

            _ = await ctx.send(
                f"{t} {balance} {discord.PartialEmoji(name="starbit",id=1349479957868318810)} starbits"
            )

    @star.command("claim")
    async def star_claim(self, ctx: commands.Context):
        """Claim your daily Starbits"""
        async with get_session() as session:
            svc = EconomyService.from_session(session)
            usr_obj = await svc.get(user.id)
            balance = 0
            if usr_obj is not None:
                balance = usr_obj.balance
            else:
                pass
