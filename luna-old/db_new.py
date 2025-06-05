import contextlib
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Optional

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

DATABASE_URL = "sqlite+aiosqlite:///database.db"

engine = create_async_engine(DATABASE_URL, future=True)


async def init_db():
    """|coro|
    Initialize the database by creating the tables.

    This function will create the tables defined in the SQLModel metadata
    if they do not already exist. If the tables do already exist, this
    function will do nothing.

    This function is idempotent and can be safely called multiple times.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def destroy_db():
    """|coro|
    Destroy the database by dropping all tables.

    This function drops all the tables defined in the SQLModel metadata.
    It should be used with caution, as this will result in the loss of all data
    stored in the database. This function is idempotent and can be safely called multiple times.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@contextlib.asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """|coro|
    Asynchronous generator that yields an :class:`AsyncSession` object.

    This function is an asynchronous generator that yields an :class:`AsyncSession` object.
    It is meant to be used as an asynchronous context manager in an ``async with`` statement.
    Example:

    .. code-block:: python

        async with get_session() as session:
            # Do something with session

    The session will be properly closed when the context manager is exited.
    """
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        session: AsyncSession
        try:
            yield session
        finally:
            await session.rollback()


class ServerConfig(SQLModel, table=True):
    ServerID: Optional[int] = Field(default=None, primary_key=True)
    # ID of the channel where the bot sends welcome messages
    WelcomeChannelID: Optional[int] = Field(default=None)
    # ID of the voice channel where the bot creates temporary voice channels
    VoiceCreationChannelID: Optional[int] = Field(default=None)
    # Whether the bot reacts with emoji to messages that match a predefined pattern
    # e.g. we react with the french flag to any message containing "fr"
    ReactionToggle: bool = Field(default=True)


class UserConfig(SQLModel, table=True):
    UserID: int = Field(default=None, primary_key=True)
    TempVoiceChannelName: Optional[str] = Field(default=None)
    Starbits: int = Field(default=0)
    # Timestamp of the next time the user can collect starbits
    StarbitsNext: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TempChannel(SQLModel, table=True):
    # ID of the temporary voice channel
    ChannelID: int = Field(default=None, primary_key=True)
    # ID of the guild to which the temporary voice channel belongs (probably redundant)
    GuildID: int


class ReactionRole(SQLModel, table=True):
    ReactRoleID: int = Field(default=None, primary_key=True)
    # ID of the message to which the reaction is attached
    MessageID: int
    # ID of the channel to which the message belongs
    ChannelID: int
    # The ID of the role to assign when the reaction is clicked
    RoleID: int
    # The emoji to react with & which we want to listen for
    Emoji: str


class AutoRole(SQLModel, table=True):
    AutoRoleID: int = Field(default=None, primary_key=True)
    # ID of the guild to which the role belongs
    GuildID: int
    # The ID of the role to assign when a user joins
    RoleID: int


async def get_server_config(
    session: AsyncSession, server_id: int
) -> Optional[ServerConfig]:
    """|coro|
    Retrieves a server's configuration from the database.

    Args:
        server_id: The ID of the server to retrieve the configuration for.

    Returns:
        The server's configuration, or None if the server has no configuration.
    """
    server_config = await session.get(ServerConfig, server_id)
    return server_config


async def get_server_config_or_default(
    session: AsyncSession, server_id: int
) -> ServerConfig:
    """|coro|
    Retrieves a server's configuration from the database, creating a default configuration if none exists.

    Args:
        server_id: The ID of the server to retrieve or create the configuration for.

    Returns:
        The server's configuration, creating and returning a default configuration if the server has none.
    """
    server_config = await session.get(ServerConfig, server_id)
    if server_config is None:
        server_config = ServerConfig(ServerID=server_id)
        session.add(server_config)
        await session.commit()
        await session.refresh(server_config)
    return server_config


async def update_server_config(session: AsyncSession, server_id: int, **kwargs) -> None:
    """|coro|
    Updates a server's configuration in the database.

    Args:
        server_id: The ID of the server to update the configuration for.
        **kwargs: Key-value pairs representing the configuration fields to be updated.

    Returns:
        None
    """
    server_config = await get_server_config_or_default(session, server_id)
    for key, value in kwargs.items():
        setattr(server_config, key, value)
    session.add(server_config)
    await session.commit()


async def get_user_config(session: AsyncSession, user_id: int) -> Optional[UserConfig]:
    """|coro|
    Retrieves a user's configuration from the database.

    Args:
        user_id: The ID of the user to retrieve the configuration for.

    Returns:
        The user's configuration, or None if the user has no configuration.
    """
    user_config = await session.get(UserConfig, user_id)
    return user_config


async def get_user_config_or_default(session: AsyncSession, user_id: int) -> UserConfig:
    """|coro|
    Retrieves a user's configuration from the database, creating a default configuration if none exists.

    Args:
        user_id: The ID of the user to retrieve or create the configuration for.

    Returns:
        The user's configuration, creating and returning a default configuration if the user has none.
    """
    user_config = await get_user_config(session, user_id)
    if user_config is None:
        user_config = UserConfig(UserID=user_id)
        session.add(user_config)
        await session.commit()
        await session.refresh(user_config)
    return user_config


async def get_all_user_ids(session: AsyncSession) -> List[int]:
    """|coro|
    Retrieves all user IDs from the database.

    Returns:
        A list of all user IDs.
    """
    return (await session.exec(select(UserConfig.UserID))).all()


async def update_user_config(session: AsyncSession, user_id: int, **kwargs) -> None:
    """
    |coro|
    Updates a user's configuration in the database.

    Args:
        user_id: The ID of the user whose configuration is to be updated.
        **kwargs: Key-value pairs representing the configuration fields to be updated.

    Returns:
        None
    """
    user_config = await get_user_config_or_default(session, user_id)
    for key, value in kwargs.items():
        setattr(user_config, key, value)
    session.add(user_config)
    await session.commit()


async def is_temp_channel(session: AsyncSession, channel_id: int) -> bool:
    """|coro|
    Checks if a channel is a temporary channel.

    Args:
        channel_id: The ID of the channel to check.

    Returns:
        True if the channel is a temporary channel, False otherwise.
    """
    temp_channel = await session.get(TempChannel, channel_id)
    return temp_channel is not None


async def create_temp_channel(
    session: AsyncSession, guild_id: int, channel_id: int
) -> None:
    """|coro|
    Creates a temporary channel in the database.

    Args:
        guild_id: The ID of the guild that the temporary channel is in.
        channel_id: The ID of the temporary channel.

    Returns:
        None
    """
    temp_channel = TempChannel(ChannelID=channel_id, GuildID=guild_id)
    session.add(temp_channel)
    await session.commit()


async def delete_temp_channel(session: AsyncSession, channel_id: int) -> None:
    """|coro|
    Deletes a temporary channel from the database.

    Args:
        channel_id: The ID of the temporary channel to delete.

    Returns:
        None
    """
    temp_channel = await session.get(TempChannel, channel_id)
    if temp_channel is not None:
        await session.delete(temp_channel)
        await session.commit()


async def get_active_temp_channels(
    session: AsyncSession, guild_id: int
) -> List[TempChannel]:
    """|coro|
    Retrieves all active temporary channels in a guild.

    Args:
        guild_id: The ID of the guild to retrieve the temporary channels from.

    Returns:
        A list of all active temporary channels in the guild.
    """
    return (
        await session.exec(select(TempChannel).where(TempChannel.GuildID == guild_id))
    ).all()


async def get_reaction_roles(session: AsyncSession) -> List[ReactionRole]:
    """|coro|
    Retrieves all reaction roles.

    Args:
        session: The database session to use.

    Returns:
        A list of all reaction roles (global)
    """
    return (await session.exec(select(ReactionRole))).all()


async def get_reaction_roles_by_channel(
    session: AsyncSession, channel_id: int
) -> List[ReactionRole]:
    """|coro|
    Retrieves all reaction roles in a guild.

    Args:
        session: The database session to use.
        channel_id: The ID of the guild to retrieve the reaction roles from.

    Returns:
        A list of all reaction roles in the guild.
    """
    return (
        await session.exec(
            select(ReactionRole).where(ReactionRole.ChannelID == channel_id)
        )
    ).all()


async def get_reaction_roles_by_message(
    session: AsyncSession, message_id: int
) -> List[ReactionRole]:
    """|coro|
    Retrieves all reaction roles associated with a message.

    Args:
        session: The database session to use.
        message_id: The ID of the message to retrieve the reaction roles from.

    Returns:
        A list of all reaction roles associated with the message.
    """
    return (
        await session.exec(
            select(ReactionRole).where(ReactionRole.MessageID == message_id)
        )
    ).all()


async def get_reaction_roles_by_role(
    session: AsyncSession, role_id: int
) -> List[ReactionRole]:
    """|coro|
    Retrieves all reaction roles associated with a role.

    Args:
        session: The database session to use.
        role_id: The ID of the role to retrieve the reaction roles from.

    Returns:
        A list of all reaction roles associated with the role.
    """
    return (
        await session.exec(select(ReactionRole).where(ReactionRole.RoleID == role_id))
    ).all()


async def get_reaction_role_by_emoji_and_message(
    session: AsyncSession, message_id: int, emoji: str
) -> Optional[ReactionRole]:
    """
    |coro|
    Retrieves a reaction role by emoji and message ID.

    Args:
        session: The database session to use.
        message_id: The ID of the message to retrieve the reaction role from.
        emoji: The emoji associated with the reaction role.

    Returns:
        The reaction role associated with the given emoji and message ID, or None if not found.
    """
    return (
        await session.exec(
            select(ReactionRole).where(
                ReactionRole.MessageID == message_id, ReactionRole.Emoji == emoji
            )
        )
    ).first()


async def create_reaction_role(
    session: AsyncSession, channel_id: int, message_id: int, role_id: int, emoji: str
) -> None:
    """|coro|
    Creates a new reaction role in the database.

    Args:
        session: The database session to use.
        channel_id: The ID of the channel that the reaction role is associated with.
        message_id: The ID of the message that the reaction role is associated with.
        role_id: The ID of the role that the reaction role grants.
        emoji: The emoji associated with the reaction role.

    Returns:
        None
    """
    reaction_role = ReactionRole(
        ChannelID=channel_id, MessageID=message_id, RoleID=role_id, Emoji=emoji
    )
    session.add(reaction_role)
    await session.commit()


async def delete_reaction_role(session: AsyncSession, reaction_role_id: int) -> None:
    """|coro|
    Deletes a reaction role from the database.

    Args:
        session: The database session to use.
        reaction_role_id: The ID of the reaction role to delete.

    Returns:
        None
    """
    reaction_role = await session.get(ReactionRole, reaction_role_id)
    if reaction_role is not None:
        await session.delete(reaction_role)
        await session.commit()


async def delete_reaction_roles_by_message(
    session: AsyncSession, message_id: int
) -> None:
    """|coro|
    Deletes all reaction roles associated with a message.

    Args:
        session: The database session to use.
        message_id: The ID of the message to delete the reaction roles from.

    Returns:
        None
    """
    reaction_roles = await get_reaction_roles_by_message(session, message_id)
    for reaction_role in reaction_roles:
        await session.delete(reaction_role)
    await session.commit()


async def delete_reaction_roles_by_role(session: AsyncSession, role_id: int) -> None:
    """|coro|
    Deletes all reaction roles associated with a role.

    Args:
        session: The database session to use.
        role_id: The ID of the role to delete the reaction roles from.

    Returns:
        None
    """
    reaction_roles = await get_reaction_roles_by_role(session, role_id)
    for reaction_role in reaction_roles:
        await session.delete(reaction_role)
    await session.commit()


async def update_reaction_role(
    session: AsyncSession, reaction_role_id: int, **kwargs
) -> None:
    reaction_role = await session.get(ReactionRole, reaction_role_id)
    """
    |coro|
    Updates a reaction role's attributes in the database.

    Args:
        session: The database session to use.
        reaction_role_id: The ID of the reaction role to update.
        **kwargs: Key-value pairs representing the ReactionRole fields to be updated.

    Returns:
        None
    """
    for key, value in kwargs.items():
        setattr(reaction_role, key, value)
    session.add(reaction_role)
    await session.commit()


async def get_auto_roles_by_guild(
    session: AsyncSession, guild_id: int
) -> List[AutoRole]:
    """|coro|
    Retrieves all auto roles in a guild.

    Args:
        session: The database session to use.
        guild_id: The ID of the guild to retrieve the auto roles from.

    Returns:
        A list of all auto roles in the guild.
    """
    return (
        await session.exec(select(AutoRole).where(AutoRole.GuildID == guild_id))
    ).all()


async def create_auto_role(session: AsyncSession, guild_id: int, role_id: int) -> None:
    """|coro|
    Creates a new auto role in the database.

    Args:
        session: The database session to use.
        guild_id: The ID of the guild that the auto role is associated with.
        role_id: The ID of the role that the auto role grants.

    Returns:
        None
    """
    auto_role = AutoRole(GuildID=guild_id, RoleID=role_id)
    session.add(auto_role)
    await session.commit()


async def delete_auto_role(session: AsyncSession, auto_role_id: int) -> None:
    """|coro|
    Deletes an auto role from the database.

    Args:
        session: The database session to use.
        auto_role_id: The ID of the auto role to delete.

    Returns:
        None
    """
    auto_role = await session.get(AutoRole, auto_role_id)
    if auto_role is not None:
        await session.delete(auto_role)
        await session.commit()


async def delete_auto_roles_by_guild(session: AsyncSession, guild_id: int) -> None:
    """|coro|
    Deletes all auto roles associated with a guild.

    Args:
        session: The database session to use.
        guild_id: The ID of the guild to delete the auto roles from.

    Returns:
        None
    """
    auto_roles = await get_auto_roles_by_guild(session, guild_id)
    for auto_role in auto_roles:
        await session.delete(auto_role)
    await session.commit()


if __name__ == "__main__":
    import asyncio

    asyncio.run(init_db())
