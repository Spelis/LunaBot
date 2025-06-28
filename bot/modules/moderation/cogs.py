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
        embed_provider: EmbedProvider,
        reason: str,
        warn_id: int,
    ) -> bool:
        try:
            dm = await user.create_dm()
            await dm.send(
                embed=embed_provider.get_action_embed(ActionType.WARN, reason)
            )
            self.logger.info(f"DM sent to {user} (Warn #{warn_id}).")
            return True
        except (discord.Forbidden, discord.HTTPException) as e:
            self.logger.warning(
                f"Failed to DM {user} (Warn #{warn_id}) due to {type(e).__name__}: {e}"
            )
            return False

    async def _send_feedback(
        self,
        ctx: commands.Context,
        user: discord.Member,
        embed: discord.Embed,
        dm_sent: bool,
        warn_id: int,
    ):
        fallback_message = (
            f"{ctx.author.mention} {user.mention}\n"
            "-# User didn't receive a DM due to privacy settings. "
            "Feedback has been sent here publicly."
        )

        try:
            if dm_sent:
                await ctx.reply(embed=embed, ephemeral=True)
                self.logger.debug(f"Ephemeral feedback sent (Warn #{warn_id}).")
            else:
                if ctx.channel.permissions_for(ctx.guild.me).send_messages:
                    await ctx.channel.send(
                        content=fallback_message,
                        embed=embed,
                        view=DismissibleByMentioned(),
                    )
                    self.logger.debug(
                        f"Fallback public feedback sent (Warn #{warn_id})."
                    )
                else:
                    await ctx.reply(embed=embed, ephemeral=True)
                    self.logger.debug(
                        f"No send permission, fallback to ephemeral (Warn #{warn_id})."
                    )
        except (discord.Forbidden, discord.HTTPException) as e:
            self.logger.error(
                f"Failed to send feedback for Warn #{warn_id} in {ctx.channel}: {type(e).__name__}: {e}",
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

        warn_id: int
        embed_provider: EmbedProvider

        async with get_session() as session:
            warn = await WarnService(session).create(ctx.guild, ctx.author, user, reason)  # type: ignore
            warn_id = warn.id

        embed_provider = EmbedProviderImpl.with_context(ctx.author, user, ctx.guild)  # type: ignore

        feedback_embed = embed_provider.get_feedback_embed(ActionType.WARN, reason)

        dm_sent = await self._try_dm(user, embed_provider, reason, warn_id)
        await self._send_feedback(ctx, user, feedback_embed, dm_sent, warn_id)

        try:
            logged = await self._log(ctx.guild, embed_provider, ActionType.WARN, reason)
            if logged:
                self.logger.info(f"Successfully logged action (Warn #{warn_id}).")
            else:
                self.logger.warning(
                    f"Failed to log action (Warn #{warn_id}). Log channel likely missing or invalid."
                )
        except Exception as e:
            self.logger.error(
                f"Unexpected error while logging warn #{warn_id}: {type(e)} - {e}",
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
