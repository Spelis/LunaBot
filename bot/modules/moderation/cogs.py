import datetime
from logging import Logger
import dateparser

import discord
from discord.ext import commands

from bot.database import get_session
from bot.luna import LunaBot

from .embeds import EmbedProviderImpl, EmbedProvider, ActionType
from .services import WarnService, SettingsService, TimeoutService
from .views import DismissibleByMentioned


class ModerationCog(commands.Cog):
    logger: Logger
    bot: LunaBot

    def __init__(self, bot: LunaBot):
        self.bot = bot
        self.logger = self.bot.logger.getChild("luna.moderation")

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
            try:
                log_channel = guild.get_channel(
                    log_channel_id
                ) or await guild.fetch_channel(log_channel_id)
            except (
                discord.errors.NotFound,
                discord.errors.Forbidden,
                discord.errors.HTTPException,
                discord.errors.InvalidData,
            ):
                log_channel = None
                # If-statement below handles fetch errors when log_channel is None
            if log_channel is None or not isinstance(log_channel, discord.TextChannel):
                self.logger.warning(
                    "Could not find log channel for guild %s, setting it to null.",
                    guild.id,
                )
                await settings_service.set_logging_channel(guild, None)
                return False
            await log_channel.send(embed=ep.get_log_embed(action_type, message))
            return True

    async def _try_dm(
        self,
        user: discord.Member,
        ep: EmbedProvider,
        action_type: ActionType,
        reason: str,
        infraction_id: int,
    ) -> bool:
        try:
            dm = await user.create_dm()
            await dm.send(embed=ep.get_action_embed(action_type, reason))
            self.logger.info(
                f"DM sent to {user} ({action_type.name.capitalize()} #{infraction_id})."
            )
            return True
        except (discord.Forbidden, discord.HTTPException) as e:
            self.logger.warning(
                f"Failed to DM {user} ({action_type.name.capitalize()} #{infraction_id}) due to {type(e).__name__}: {e}"
            )
            return False

    async def _send_feedback(
        self,
        ctx: commands.Context,
        user: discord.Member,
        embed: discord.Embed,
        action_type: ActionType,
        dm_sent: bool,
        infraction_id: int,
    ):
        fallback_message = (
            f"{ctx.author.mention} {user.mention}\n"
            "-# User didn't receive a DM due to privacy settings. "
            "Feedback has been sent here publicly."
        )

        try:
            if dm_sent:
                await ctx.reply(embed=embed, ephemeral=True)
                self.logger.debug(
                    f"Ephemeral feedback sent ({action_type.name.capitalize()} #{infraction_id})."
                )
            else:
                if (
                    ctx.guild is not None
                    and ctx.channel.permissions_for(ctx.guild.me).send_messages
                ):
                    await ctx.channel.send(
                        content=fallback_message,
                        embed=embed,
                        view=DismissibleByMentioned(),
                    )
                    self.logger.debug(
                        f"Fallback public feedback sent ({action_type.name.capitalize()} #{infraction_id})."
                    )
                else:
                    await ctx.reply(embed=embed, ephemeral=True)
                    self.logger.debug(
                        f"No send permission, fallback to ephemeral ({action_type.name.capitalize()} #{infraction_id})."
                    )
        except (discord.Forbidden, discord.HTTPException) as e:
            self.logger.error(
                f"Failed to send feedback for {action_type.name.capitalize()} #{infraction_id} in {ctx.channel}: {type(e).__name__}: {e}",
                exc_info=e,
            )

    async def _infraction_callback(
        self,
        ctx: commands.Context,
        guild: discord.Guild,
        moderator: discord.Member,
        user: discord.Member,
        reason: str,
        action_type: ActionType,
        infraction_id: int,
        duration: datetime.timedelta | None = None,
    ):
        """
        Handles callback for creating an infraction.
        """
        ep = EmbedProviderImpl.with_context(guild, moderator, user, duration)  # type: ignore

        feedback_embed = ep.get_feedback_embed(action_type, reason)

        dm_sent = await self._try_dm(user, ep, action_type, reason, infraction_id)
        await self._send_feedback(
            ctx, user, feedback_embed, action_type, dm_sent, infraction_id
        )

        try:
            logged = await self._log(guild, ep, action_type, reason)
            if logged:
                self.logger.info(
                    f"Successfully logged action ({action_type.name.capitalize()} #{infraction_id})."
                )
            else:
                self.logger.warning(
                    f"Failed to log action ({action_type.name.capitalize()} #{infraction_id}). Log channel likely missing or invalid."
                )
        except Exception as e:
            self.logger.error(
                f"Unexpected error while logging {action_type.name.lower()} #{infraction_id}: {type(e)} - {e}",
                exc_info=e,
            )

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
        assert ctx.guild is not None
        await ctx.defer(ephemeral=True)

        async with get_session() as session:
            warn = await WarnService(session).create(ctx.guild, ctx.author, user, reason)  # type: ignore
            warn_id = warn.id

        moderator: discord.Member = ctx.author  # type: ignore - Type annotations suggest author could be discord.User, but I doubt that.
        await self._infraction_callback(
            ctx, ctx.guild, moderator, user, reason, ActionType.WARN, warn_id
        )

    def try_parse_date(self, date: str) -> datetime.timedelta:
        if len(date) == 0:
            raise commands.CommandError("No date given.")

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        parsed = dateparser.parse(
            date,
            settings={
                "RELATIVE_BASE": now,
                "RETURN_AS_TIMEZONE_AWARE": True,
                "PREFER_DATES_FROM": "future",
            },
        )
        if parsed is None:
            raise ValueError("Unable to parse date.")
        td = parsed - now
        if now + td < now:
            raise ValueError(
                "Date cannot be in the past. Try adding `in` before the duration, e.g: `in 1w`, `in one week`"
            )
        return td

    @commands.hybrid_command(
        name="timeout",
        aliases=["mute"],
        usage="timeout <user> <time> <reason>",
        description="Warns a user",
    )
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def _timeout(
        self,
        ctx: commands.Context,
        user: discord.Member,
        duration: str = "1w",
        reason: str = "No reason given.",
    ):
        assert ctx.guild is not None
        await ctx.defer(ephemeral=True)

        try:
            punishment_duration: datetime.timedelta = self.try_parse_date(duration)
        except ValueError as e:
            await ctx.reply(f"Error: {e}", ephemeral=True)
            return

        try:
            await user.timeout(punishment_duration, reason=reason)
        except discord.Forbidden as e:
            self.logger.error(
                f"Failed to timeout user {user.id} in guild {ctx.guild.id}: {type(e)} - {e}",
                exc_info=e,
            )
            raise e

        async with get_session() as session:
            timeout = await TimeoutService(session).create(ctx.guild, ctx.author, user, reason)  # type: ignore
            timeout_id = timeout.id

        moderator: discord.Member = ctx.author  # type: ignore - Type annotations suggest author could be discord.User, but I doubt that.
        await self._infraction_callback(
            ctx,
            ctx.guild,
            moderator,
            user,
            reason,
            ActionType.TIMEOUT,
            timeout_id,
            punishment_duration,
        )

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        match error:
            case commands.CommandOnCooldown():
                await ctx.reply(
                    f"You have to wait **{error.retry_after:.2f}s** before using this command again.",
                    ephemeral=True,
                )
            case discord.Forbidden():
                await ctx.reply(
                    "I don't have the permissions to execute this command.\nMake sure the bot can moderate members in the server, and the moderated member's highest role is lower than the bot's highest role.",
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
