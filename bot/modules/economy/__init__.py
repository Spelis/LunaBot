from bot.database import init_db
from bot.luna import LunaBot

from .cogs import Economy, Gambling
from .models import EconomyModel


async def setup(bot: LunaBot):
    await init_db()
    await bot.add_cog(Economy(bot))
    await bot.add_cog(Gambling(bot))
