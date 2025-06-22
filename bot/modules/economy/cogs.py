import datetime
import random

import discord
from discord.ext import commands

from bot.database import get_session
from bot.luna import LunaBot

from .services import EconomyService

STARBIT_EMOJI = discord.PartialEmoji(name="starbit", id=1349479957868318810)


class Economy(commands.Cog):
    CLAIM_DELAY = datetime.timedelta(days=1)

    def __init__(self, bot: LunaBot) -> None:
        self.bot: LunaBot = bot

    @commands.hybrid_group("star")
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def star(self, ctx: commands.Context):
        """Economy commands"""
        if ctx.invoked_subcommand is None:
            await self.star_balance(ctx)

    @star.command("balance")  # type: ignore - type checker doesn't command groups I guess.
    async def star_balance(
        self, ctx: commands.Context, user: discord.Member | discord.User | None = None
    ):
        """Check your starbit balance"""
        user = user or ctx.author
        sentence_beginning: str = (
            "You have" if user.id == ctx.author.id else f"{user.mention} has"
        )
        async with get_session() as session:
            svc = EconomyService.from_session(session)
            account = await svc.get_or_create(user.id)
            await ctx.send(
                f"{sentence_beginning} {account.balance} {STARBIT_EMOJI} starbits"
            )

    @star.command("claim")  # This one's fine though for some reason.
    async def _star_claim(self, ctx: commands.Context):
        """Claim your daily Starbits"""
        async with get_session() as session:
            svc = EconomyService.from_session(session)
            account = await svc.get_or_create(ctx.author.id)
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            if now - account.last_claim < self.CLAIM_DELAY:
                await ctx.send(
                    f"You have already claimed your daily starbits! You can claim again <t:{round((account.last_claim + self.CLAIM_DELAY).timestamp())}:R>"
                )
                return
            amount = random.randint(1, 10)
            was_boosted = False
            if random.random() < 0.1:  # 10% chance
                amount *= 2
                was_boosted = True
            account.balance += amount
            account.last_claim = now
            await svc.update(account)
            if was_boosted:
                return
            await ctx.send(
                ("✨ LUCKY DAY! " if was_boosted else "")
                + f"You have claimed {amount} {STARBIT_EMOJI} starbits. You can claim again <t:{round((now + self.CLAIM_DELAY).timestamp())}:R>\nYour balance is now {account.balance} {STARBIT_EMOJI} starbits."
            )


class ChanceMultiplier:
    def __init__(self, multiplier: float, message: str):
        self.multiplier = multiplier
        self.message = message


class Gambling(commands.Cog):
    # This is a map of threshold -> amount
    chance: dict[int, ChanceMultiplier] = {
        # Yes, I just hardcoded emoji like it's 1999, cry about it
        5: ChanceMultiplier(10, "🎰 JACKPOT! 10x"),
        10: ChanceMultiplier(3, "✨ Big Win! 3x"),
        20: ChanceMultiplier(1.5, "🍻 Small Win. 1.5x"),
        70: ChanceMultiplier(-1, "💔 Loss! -100%"),
        100: ChanceMultiplier(-1.25, "💥 Critical Loss! -125%"),
    }

    def __init__(self, bot: LunaBot) -> None:
        self.bot: LunaBot = bot

    @commands.hybrid_group(
        "gamble", usage="gamble [game] ...", description="Gamble your starbits"
    )
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def gamble(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send("Please choose a game!", ephemeral=True)

    @gamble.command(
        "chance",
        usage="gamble chance <amount>",
        description="Gamble your starbits in a game of chance.",
    )
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def _chance(self, ctx: commands.Context, amount: int):
        async with get_session() as session:
            svc = EconomyService.from_session(session)
            account = await svc.get_or_create(ctx.author.id)
            if amount > account.balance:
                await ctx.send(
                    f"Insufficient funds. you have {account.balance} {STARBIT_EMOJI} starbits."
                )
                return
            random_chance = random.randint(1, 100)
            key: int = min(self.chance.keys(), key=lambda x: abs(x - random_chance))
            multiplier: ChanceMultiplier = self.chance[key]
            account.balance += amount * multiplier.multiplier
            await svc.update(account)
            await ctx.send(f"{multiplier.message} ({amount * multiplier.multiplier})")
