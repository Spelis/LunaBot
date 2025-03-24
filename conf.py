from datetime import datetime, timezone

import db_new


async def create_schema() -> None:
    await db_new.init_db()


async def set_server_welcome_channel(guild_id: int, welcome_channel_id: int) -> None:
    async with db_new.get_session() as session:
        await db_new.update_server_config(
            session, guild_id, WelcomeChannelID=welcome_channel_id
        )


async def set_server_voice_creation_channel(
    guild_id: int, voice_creation_channel_id: int
) -> None:
    async with db_new.get_session() as session:
        await db_new.update_server_config(
            session, guild_id, VoiceCreationChannelID=voice_creation_channel_id
        )


async def set_server_reaction_toggle(guild_id: int, reaction_toggle: bool) -> None:
    async with db_new.get_session() as session:
        await db_new.update_server_config(
            session, guild_id, ReactionToggle=reaction_toggle
        )
        
async def get_server_reaction_toggle(guild_id: int) -> None:
    async with db_new.get_session() as session:
        return (await db_new.get_server_config_or_default(
            session, guild_id
        )).ReactionToggle


async def get_welcome_roles(guild_id: int) -> list[int]:
    async with db_new.get_session() as session:
        return [
            r.RoleID for r in await db_new.get_auto_roles_by_guild(session, guild_id)
        ]


async def set_welcome_roles(guild_id: int, welcome_roles: list[int]) -> None:
    """
    Sets the welcome roles for a server.

    Args:
        guild_id (int): ID of the server.
        welcome_roles (list[int]): List of role IDs to set as welcome roles.

    Returns:
        None
    """
    async with db_new.get_session() as session:
        existing = [
            r.RoleID for r in await db_new.get_auto_roles_by_guild(session, guild_id)
        ]
        for role_id in welcome_roles:
            if role_id in existing:
                continue
            await db_new.create_auto_role(session, guild_id, role_id)


async def get_server_config(guild_id: int) -> dict:
    async with db_new.get_session() as session:
        server_config = await db_new.get_server_config_or_default(session, guild_id)
        return {
            "guild_id": server_config.ServerID,
            "welcome_channel_id": server_config.WelcomeChannelID,
            "voice_creation_channel_id": server_config.VoiceCreationChannelID,
            "reaction_toggle": server_config.ReactionToggle,
            "welcome_roles": await get_welcome_roles(guild_id),
            "react_roles": await get_reactroles(guild_id),
        }


async def get_user_config(user_id: int) -> dict:
    async with db_new.get_session() as session:
        user_data = await db_new.get_user_config_or_default(session, user_id)
        return {
            "ChanName": user_data.TempVoiceChannelName,
            "Starbits": user_data.Starbits,
            "StarbitsNextCollect": user_data.StarbitsNext.timestamp(),
        }


async def get_reactroles(guildid: int) -> list[dict]:
    async with db_new.get_session() as session:
        return [
            {
                "message_id": r.MessageID,
                "emoji": r.Emoji,
                "role_id": r.RoleID,
            }
            for r in await db_new.get_reaction_roles_by_guild(session, guildid)
        ]


async def set_starbits(user_id: int, starbits: int) -> None:
    async with db_new.get_session() as session:
        await db_new.update_user_config(session, user_id, Starbits=starbits)


async def set_starbit_collection(user_id: int, timestamp: int) -> None:
    async with db_new.get_session() as session:
        await db_new.update_user_config(
            session,
            user_id,
            StarbitsNext=datetime.fromtimestamp(timestamp, timezone.utc),
        )


async def add_starbits(user_id: int, starbits: int) -> None:
    async with db_new.get_session() as session:
        user_data = await db_new.get_user_config_or_default(session, user_id)
        user_data.Starbits += starbits
        session.add(user_data)
        await session.commit()


async def set_channel_name(user_id: int, chan_name: str) -> None:
    async with db_new.get_session() as session:
        await db_new.update_user_config(
            session, user_id, TempVoiceChannelName=chan_name
        )
