from bot.database import init_db
from bot.luna import LunaBot

from .cogs import HelloWorld

# This needs to be imported to register the model with SQLModel when we call init_db
from .models import ExampleModel  # pylint: disable=unused-import # noqa


async def setup(bot: LunaBot):
    await init_db()
    await bot.add_cog(HelloWorld(bot))
