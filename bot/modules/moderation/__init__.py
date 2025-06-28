from bot.database import init_db
from bot.luna import LunaBot

from .cogs import ModerationCog

from .models import *  # pylint: disable=unused-import # noqa


async def setup(bot: LunaBot):
    await init_db()
    await bot.add_cog(ModerationCog(bot))
