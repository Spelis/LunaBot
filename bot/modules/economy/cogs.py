from enum import Enum, auto, StrEnum, IntEnum
from typing import Literal
import datetime
import random

import discord
from discord import app_commands
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

    @star.command("balance")
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

    @star.command("claim")
    async def _star_claim(self, ctx: commands.Context):
        """Claim your daily Starbits"""
        async with get_session() as session:
            svc = EconomyService.from_session(session)
            account = await svc.get_or_create(ctx.author.id)
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            if now - account.utc_last_claim < self.CLAIM_DELAY:
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
            await ctx.send(
                ("✨ LUCKY DAY! " if was_boosted else "")
                + f"You have claimed {amount} {STARBIT_EMOJI} starbits. You can claim again <t:{round((now + self.CLAIM_DELAY).timestamp())}:R>\nYour balance is now {account.balance} {STARBIT_EMOJI} starbits."
            )

    @star.command("steal")
    @commands.cooldown(2, 120, commands.BucketType.member)
    @commands.guild_only()
    async def _star_steal(self, ctx: commands.Context, victim: discord.Member):
        await ctx.defer()
        """Steal starbits from another user"""
        victim_roll = random.randint(1, 20)
        attacker_roll = random.randint(1, 20)
        roll_delta = max(victim_roll, attacker_roll) - min(victim_roll, attacker_roll)
        async with get_session() as session:
            svc = EconomyService.from_session(session)
            victim_account = await svc.get_or_create(victim.id)

            if victim_account.balance <= 0:
                await ctx.send(f"{victim.mention} has no starbits to steal!")
                return

            attacker_account = await svc.get_or_create(ctx.author.id)

            # The attacker shouldn't be allowed to gain more than 2x their own starbits
            max_gain_balance = 2 * attacker_account.balance
            cap = min(1, max_gain_balance / victim_account.balance)
            percentage = min(cap, max(0, roll_delta / 20))

            steal_amount = abs(int(victim_account.balance * percentage))
            fine_amount = max(
                int(steal_amount / 10), abs(int(attacker_account.balance * percentage))
            )  # wtf
            if attacker_roll > 10 and attacker_roll > victim_roll:
                # Steal
                victim_account.balance -= steal_amount
                attacker_account.balance += steal_amount
                await svc.update(victim_account)
                await svc.update(attacker_account)
                await ctx.send(
                    f"{ctx.author.mention} has stolen {steal_amount} {STARBIT_EMOJI} starbits from {victim.mention}!"
                )
            else:
                # Caught - fine
                attacker_account.balance -= fine_amount
                await svc.update(attacker_account)
                await ctx.send(
                    f"{ctx.author.mention} has been caught stealing starbits from {victim.mention} and has been fined {fine_amount} {STARBIT_EMOJI}!"
                )

    # # I was going to implement these, but there's going to be issues in larger servers in regards to checking the balance of every damn member.
    # # As such, I suggest we first keep track of which guilds members are in within our DB and filter based on that using a where clause in the repository.
    # # Benefits of an event driven system is that we don't need to call to discord's API to figure that out, as the gateway tells us.
    # # That being said, I'm not sure if this will be worth it. Might just resort to using the API to turn members into IDs, select based on a super massive where clause, and then order by balance.
    # @star.group("top")
    # async def star_top(self, ctx: commands.Context):
    #     """Check the top 10 starbit holders"""
    #     if ctx.invoked_subcommand is None:
    #         await self.star_top_server(ctx)
    #
    # @star_top.command("server")
    # async def star_top_server(self, ctx: commands.Context):
    #     """Check the top 10 starbit holders in this server"""
    #     pass
    #
    # @star_top.command("global")
    # async def star_top_global(self, ctx: commands.Context):
    #     """Check the top 10 starbit holders globally"""
    #     pass

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        match error:
            case commands.CommandOnCooldown():
                seconds = error.retry_after
                now = datetime.datetime.now(tz=datetime.timezone.utc)
                then = now + datetime.timedelta(seconds=seconds)
                await ctx.reply(
                    f"You are on a cooldown. You can use this command again <t:{round(then.timestamp())}:r>.",
                    ephemeral=True,
                )
            case _:
                await ctx.reply(
                    f"Failed to execute command.\n**{type(error)}**: {error}\nPlease contact bot developers or [report this issue on GitHub](https://github.com/Spelis/LunaBot/issues/new).",
                    ephemeral=True,
                )


class ChanceMultiplier:
    def __init__(self, multiplier: float, message: str):
        self.multiplier = multiplier
        self.message = message


BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}
RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}


class RouletteColor(StrEnum):
    RED = "red"
    BLACK = "black"
    GREEN = "green"


class RouletteOddEven(StrEnum):
    ODD = "odd"
    EVEN = "even"


class RouletteBetType(StrEnum):
    NUMBER = "number"
    COLOR = "color"
    ODD_EVEN = "odd_even"


class RouletteResult:
    def __init__(self, number: int) -> None:
        self.number = number
        self.color = self._get_color()

    def _get_color(self) -> RouletteColor:
        if self.number == 0:
            return RouletteColor.GREEN
        if self.number in BLACK_NUMBERS:
            return RouletteColor.BLACK
        return RouletteColor.RED

    @property
    def odd(self) -> bool:
        return self.number != 0 and self.number % 2 == 1

    @property
    def even(self) -> bool:
        return self.number != 0 and self.number % 2 == 0


def spin_roulette() -> RouletteResult:
    return RouletteResult(random.randint(0, 36))


def calculate_roulette_payout(
    bet_type: RouletteBetType,
    bet_value: RouletteColor | RouletteOddEven | int,
    result: RouletteResult,
    stake: int,
) -> int:
    """
    Calculate the payout for a game of roulette.
    Returns a positive value if the player wins, negative if they lose.

    Throws an error if you pass garbage to bet_type
    """
    if bet_type == RouletteBetType.NUMBER:
        if result.number == bet_value:
            return stake * 35
        return -stake
    elif bet_type == RouletteBetType.COLOR:
        if result.color == bet_value:
            return stake
        return -stake
    elif bet_type == RouletteBetType.ODD_EVEN:
        if bet_value == RouletteOddEven.ODD and result.odd:
            return stake
        if bet_value == RouletteOddEven.EVEN and result.even:
            return stake
        return -stake
    else:
        raise ValueError("Invalid bet type")


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
            await ctx.send(
                "Please choose a game!\n- `gamble chance 100` to gamble 100 starbits in a game of random chance. (D100 roll)\n- `gamble roulette 100 red` to gamble 100 starbits in a game of roulette, betting on red.",
                ephemeral=True,
            )

    @gamble.command(
        "chance",
        usage="gamble chance <amount>",
        description="Gamble your starbits in a game of chance.",
    )
    @commands.cooldown(5, 120, commands.BucketType.member)
    async def _chance(self, ctx: commands.Context, amount: int):
        if amount <= 0:
            await ctx.send(
                f"You must gamble at least 1 {STARBIT_EMOJI} starbits.", ephemeral=True
            )
            return
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

    @gamble.command(
        "roulette",
        usage="gamble roulette <amount> <odd|even|red|black|number>",
        description="Play roulette.",
    )
    @commands.cooldown(5, 120, commands.BucketType.member)
    async def _roulette(self, ctx, amount: int, bet: str):
        if amount <= 0:
            await ctx.send(
                f"You must gamble at least 1 {STARBIT_EMOJI} starbits.", ephemeral=True
            )
            return
        async with get_session() as session:
            svc = EconomyService.from_session(session)
            account = await svc.get_or_create(ctx.author.id)

            if amount > account.balance:
                await ctx.send(
                    f"Insufficient funds. You have {account.balance} {STARBIT_EMOJI} starbits."
                )
                return

            # Normalize bet - I don't even know why this is so unnecessarily complex, probably cause the type annotations on this method changed 4 times already.
            if bet in {str(i) for i in range(1, 37)}:
                bet_type, bet_value = RouletteBetType.NUMBER, int(bet)
            elif bet in {RouletteColor.GREEN, "green"} or (
                isinstance(bet, int) and bet == 0
            ):
                bet_type, bet_value = RouletteBetType.NUMBER, 0
            elif bet in {RouletteColor.RED, RouletteColor.BLACK, "red", "black"}:
                bet_type, bet_value = RouletteBetType.COLOR, RouletteColor(bet)
            elif bet in {RouletteOddEven.EVEN, RouletteOddEven.ODD, "even", "odd"}:
                bet_type, bet_value = RouletteBetType.ODD_EVEN, RouletteOddEven(bet)
            else:
                await ctx.send(
                    "Invalid bet. You can bet on:\n- color: red or black\n- number: 1-36\n- odd or even\n- 0 or green"
                )
                return

            result = spin_roulette()
            payout = calculate_roulette_payout(bet_type, bet_value, result, amount)

            account.balance += payout
            await svc.update(account)

            outcome = "won" if payout > 0 else "lost"
            if result.odd:
                number_kind = "Odd"
            elif result.even:
                number_kind = "Even"
            else:
                number_kind = "Neither"

            await ctx.send(
                f"You {outcome} {abs(payout)} {STARBIT_EMOJI} starbits.\n"
                + f"The roulette landed on **{result.color} {result.number} "
                + f"({number_kind})**."
            )

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        match error:
            case commands.CommandOnCooldown():
                seconds = error.retry_after
                now = datetime.datetime.now(tz=datetime.timezone.utc)
                then = now + datetime.timedelta(seconds=seconds)
                await ctx.reply(
                    f"You are on a cooldown. You can use this command again <t:{round(then.timestamp())}:r>.",
                    ephemeral=True,
                )
            case _:
                await ctx.reply(
                    f"Failed to execute command.\n**{type(error)}**: {error}\nPlease contact bot developers or [report this issue on GitHub](https://github.com/Spelis/LunaBot/issues/new).",
                    ephemeral=True,
                )
