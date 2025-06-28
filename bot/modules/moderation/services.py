from discord import Guild, Member, TextChannel
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ModerationSettings as Settings
from .models import Warning as Warn
from .repositories import WarnRepository, SettingsRepository


class SettingsService:
    repository: SettingsRepository

    def __init__(self, session: AsyncSession):
        self.repository = SettingsRepository(session)

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(session)

    async def get_existing_or_create_default(self, guild_id: int) -> Settings:
        """
        Get a guild's settings object, creating a default if it does not exist.

        Args:
            guild_id (int): The guild's ID.

        Returns:
            Settings: The guild's settings object.
        """
        s: Settings | None = await self.repository.get(guild_id)
        if s is None:
            s = Settings(guild_id=guild_id)
            await self.repository.save(s)
        return s

    async def get_logging_channel_id(self, guild: Guild) -> int | None:
        """
        Retrieves the logging channel ID for the specified guild.

        Args:
            guild (Guild): The guild to retrieve the logging channel ID for.

        Returns:
            int | None: The ID of the logging channel, or None if not set.
        """
        settings = await self.get_existing_or_create_default(guild.id)
        return settings.log_channel

    async def set_logging_channel(
        self, guild: Guild, channel: TextChannel | None
    ) -> None:
        """
        Set the logging channel for the guild.

        Args:
            guild (Guild): The guild to set the logging channel for.
            channel (TextChannel | None): The channel to set as the logging channel,
                or None to clear the logging channel.
        """
        settings = await self.get_existing_or_create_default(guild.id)
        settings.logging_channel_id = channel.id if channel else None
        await self.repository.save(settings)


class WarnService:
    repository: WarnRepository

    def __init__(self, session: AsyncSession):
        self.repository = WarnRepository(session)

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(session)

    async def create(
        self, guild: Guild, actor: Member, target: Member, reason: str
    ) -> Warn:
        warn = Warn(
            guild_id=guild.id,
            user_id=target.id,
            moderator_id=actor.id,
            reason=reason,
        )
        return await self.repository.save(warn)
