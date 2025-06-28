from logging import Logger

import discord
from discord.ext import commands

from bot.database import get_session
from bot.logs import get_logger
from bot.luna import LunaBot

from .embeds import EmbedProviderImpl, EmbedProvider, ActionType
from .services import WarnService, SettingsService
from .views import DismissibleByMentioned


class ModerationCog(commands.Cog):
    logger: Logger
    bot: LunaBot

    def __init__(self, bot: LunaBot):
        self.bot = bot
        self.logger = get_logger("luna.moderation")

    async def cog_load(self) -> None:
        # Registers a persistent view
        if not any(
            isinstance(v, DismissibleByMentioned) for v in self.bot.persistent_views
        ):
            self.bot.add_view(DismissibleByMentioned())

    async def _log(
        self,
        guild: discord.Guild,
        ep: EmbedProvider,
        action_type: ActionType,
        message: str,
    ) -> bool:
        """
        Logs the given action to the guild's moderation logging channel.

        If no logging channel is set, does nothing.

        ! Side effects: If the logging channel is not found, it is set to null.

        Args:
            guild (discord.Guild): The guild to log in.
            ep (EmbedProvider): The embed provider instance to create the log embed with.
            action_type (ActionType): The type of the action that was taken.
            message (str): The message that was given by the user who took the action.

        Returns:
            bool: True if the command exited successfully, False if something went wrong and the log channel has been cleared.
        """
        async with get_session() as session:
            settings_service = SettingsService(session)
            log_channel_id: int | None = await settings_service.get_logging_channel_id(
                guild
            )
            if log_channel_id is None:
                return True
            log_channel = guild.get_channel(
                log_channel_id
            ) or await guild.fetch_channel(log_channel_id)
            if log_channel is None or not isinstance(log_channel, discord.TextChannel):
                self.logger.warning(
                    "Could not find log channel for guild %s, setting it to null.",
                    guild.id,
                )
                await settings_service.set_logging_channel(guild, None)
                return False
            await log_channel.send(embed=ep.get_log_embed(action_type, message))
            return True

    @commands.hybrid_command(
        name="warn",
        aliases=["warning"],
        usage="warn <user> <reason>",
        description="Warns a user",
    )
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def _warn(
        self,
        ctx: commands.Context,
        user: discord.Member,
        reason: str = "No reason given.",
    ):
        """
        Warns a user.

        Implementation Details:
        1. Attempts to send a DM to the user. If it fails, feedback is sent in the channel as non-ephemeral.
        2. Creates a warning in the database, which is why we defer.

        Args:
            ctx: The invocation context.
            user: The user to warn.
            reason: The reason for the warning.

        Returns:
            None
        """
        assert ctx.guild is not None
        await ctx.defer(ephemeral=True)
        async with get_session() as session:
            warn = await WarnService(session).create(ctx.guild, ctx.author, user, reason)  # type: ignore
            warn_id: int = warn.id
        ep = EmbedProviderImpl.with_context(ctx.author, user, ctx.guild)  # type: ignore
        dm_channel = await user.create_dm()
        feedback_embed = ep.get_feedback_embed(ActionType.WARN, reason)
        respond_publicly: bool
        try:
            await dm_channel.send(embed=ep.get_action_embed(ActionType.WARN, reason))
        except (discord.errors.Forbidden, discord.errors.HTTPException) as e:
            self.logger.warning(
                f"Failed to send DM to {user.name} due to {type(e)} (Warn #{warn_id})."
            )
            respond_publicly = True
        else:
            self.logger.info(f"Successfully sent DM to {user.name} (Warn #{warn_id}).")
            respond_publicly = False
        if respond_publicly and ctx.channel.permissions_for(ctx.guild.me).send_messages:
            try:
                await ctx.channel.send(
                    content=f"{ctx.author.mention} {user.mention}\n-# User didn't receive a DM due to their privacy settings, feedback has been sent in this channel publicly instead.",
                    embed=feedback_embed,
                    view=DismissibleByMentioned(),
                )
            except (discord.errors.Forbidden, discord.errors.HTTPException) as e:
                self.logger.warning(
                    f"Failed to send message in {ctx.channel} due to {type(e)} (Warn #{warn_id}). Falling back to ephemeral."
                )
                respond_publicly = False
            else:
                self.logger.info(
                    f"Successfully sent public feedback message in {ctx.channel} (Warn #{warn_id})."
                )
        if not respond_publicly:
            try:
                await ctx.reply(
                    embed=feedback_embed,
                    ephemeral=True,
                )
            except (discord.errors.Forbidden, discord.errors.HTTPException) as e:
                self.logger.error(
                    f"Failed to send ephemeral message in {ctx.channel} due to {type(e)} (Warn #{warn_id}). All options have been attempted, user might not have received any feedback."
                )
            else:
                self.logger.info(
                    f"Successfully sent ephemeral feedback message in {ctx.channel} (Warn #{warn_id})."
                )
        try:
            result = await self._log(ctx.guild, ep, ActionType.WARN, reason)
            if result:
                self.logger.info(f"Successfully logged action (Warn #{warn_id}).")
            else:
                self.logger.warning(
                    f"Failed to log action (Warn #{warn_id}). Gracefully handled error, but log message was not sent."
                )
        except Exception as e:
            self.logger.error(
                f"Failed to log action (Warn #{warn_id}) due to {type(e)}: {e}",
                exc_info=e,
            )

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        match error:
            case commands.CommandOnCooldown():
                await ctx.reply(
                    f"You have to wait **{error.retry_after:.2f}s** before using this command again.",
                    ephemeral=True,
                )
            case _:
                await ctx.reply(
                    f"Failed to execute command.\n**{type(error)}**: {error}\nPlease contact bot developers or [report this issue on GitHub](https://github.com/Spelis/LunaBot/issues/new).",
                    ephemeral=True,
                )
                # There's 2 nested ternary expressions here, sorry not sorry. Fix it if you can be bothered.
                self.logger.error(
                    f"Failed to execute command {ctx.command} by {ctx.author} ({ctx.author.id}) in {ctx.guild if ctx.guild else 'DMs'} ({ctx.guild.id if ctx.guild else ctx.author.dm_channel.id if ctx.author.dm_channel else 'No DM Channel'}).",
                    exc_info=error,
                )
