from typing import Any
from discord.ext import commands
from ..luna import LunaBot


class NotLunaDeveloper(commands.CheckFailure):
    def __init__(self, message: str | None = None, *args: Any) -> None:
        super().__init__(
            message
            or "Command executed by non-Luna developer. If you are a Luna developer, make sure this instance has been configured with your ID in the environment variable `LUNA_DEVELOPER_IDS`",
            *args,
        )


def luna_developer_only():
    """
    A decorator that checks if the command invoker is a LunaBot developer.

    This decorator can be applied to commands to restrict their usage to
    only those users whose IDs are listed in the `LUNA_DEVELOPER_IDS` environment
    variable. If the command is invoked by a non-developer, a `NotLunaDeveloper`
    exception is raised.

    Returns:
        A command decorator that checks for developer status.
    
    Usage:
        >>> @commands.hybrid_command()
        @luna_developer_only()
        async def command(ctx):
            pass
    """

    async def predicate(ctx: commands.Context):
        if isinstance(ctx.bot, LunaBot):
            bot: LunaBot = ctx.bot
        else:
            raise RuntimeError(
                "LunaBot specific API used with non-LunaBot client instance. Unable to check developer status."
            )
        if ctx.author.id not in bot.settings.developer_ids:
            raise NotLunaDeveloper()
        return True

    return commands.check(predicate)
