from bot.luna import LunaBot

from .cogs import Developer


async def setup(bot: LunaBot):
    await bot.add_cog(Developer(bot))
