import json
from typing import Iterable

import aiosqlite

# credits to HyScript7 for teaching me sqlite

FILE = "database.db"
fetchType = aiosqlite.Cursor

schema_created: bool = False


async def create_schema() -> None:
    async with aiosqlite.connect(FILE) as conn:
        async with conn.cursor() as c:
            await c.execute(
                """
                CREATE TABLE IF NOT EXISTS serverconf (
                    IdServerconf INTEGER PRIMARY KEY,
                    WelcomeChannelId INTEGER DEFAULT NULL,
                    VoiceCreationId INTEGER DEFAULT NULL,
                    ReactionToggle INTEGER DEFAULT 1,
                    WelcomeRoles TEXT DEFAULT '[]'
                );
                """,
            )
            await c.execute(
                """
                CREATE TABLE IF NOT EXISTS userconf (
                    UserID INTEGER PRIMARY KEY,
                    ChanName TEXT DEFAULT NULL,
                    Starbits INTEGER DEFAULT 0,
                    StarbitsNextCollect INTEGER DEFAULT 0
                );
                """
            )
            await c.execute(
                """
                CREATE TABLE IF NOT EXISTS temporary_voice_channels (
                    ChannelId INTEGER PRIMARY KEY,
                    GuildId INTEGER,
                    CreatedAt INTEGER
                );
                """
            )
            await c.execute(
                """
                CREATE TABLE IF NOT EXISTS reactroles (
                    ReactRoleId INTEGER PRIMARY KEY,
                    MessageId INTEGER NOT NULL,
                    Emoji VARCHAR(10) NOT NULL,
                    RoleId INTEGER NOT NULL,
                    GuildId INTEGER NOT NULL
                );
                """
            )
            await conn.commit()


async def execute(
    query: str, *args, fetch="all"
) -> Iterable[aiosqlite.Row] | aiosqlite.Row | None:
    await create_schema()
    async with aiosqlite.connect(FILE) as conn:
        async with conn.cursor() as c:
            try:
                await c.execute(query, args)
                await conn.commit()
                if fetch == "all":
                    return await c.fetchall()
                elif fetch == "many":
                    return await c.fetchmany()
                else:
                    return await c.fetchone()
            except aiosqlite.IntegrityError:
                return


async def create_default_server_config(guild_id: int) -> None:
    await execute("INSERT INTO serverconf (IdServerconf) VALUES (?)", guild_id)


async def set_server_welcome_channel(guild_id: int, welcome_channel_id: int) -> None:
    await execute(
        "UPDATE serverconf SET WelcomeChannelId = ? WHERE IdServerconf = ?",
        welcome_channel_id,
        guild_id,
    )


async def set_server_voice_creation_channel(
    guild_id: int, voice_creation_channel_id: int
) -> None:
    await create_default_server_config(guild_id)
    await execute(
        "UPDATE serverconf SET VoiceCreationId = ? WHERE IdServerconf = ?",
        voice_creation_channel_id,
        guild_id,
    )


async def set_server_reaction_toggle(guild_id: int, reaction_toggle: int) -> None:
    await create_default_server_config(guild_id)
    await execute(
        "UPDATE serverconf SET ReactionToggle = ? WHERE IdServerconf = ?",
        reaction_toggle,
        guild_id,
    )


async def get_welcome_roles(guild_id: int) -> list[int]:
    await create_default_server_config(guild_id)
    result = await execute(
        "SELECT WelcomeRoles FROM serverconf WHERE IdServerconf = ?", guild_id
    )
    if not result:
        return []
    return json.loads(result[0][0])


async def set_welcome_roles(guild_id: int, welcome_roles: list[int]) -> None:
    """
    Sets the welcome roles for a server.

    Args:
        guild_id (int): ID of the server.
        welcome_roles (list[int]): List of role IDs to set as welcome roles.

    Returns:
        None
    """
    # Ensure a row exists (create default config)
    await create_default_server_config(guild_id)
    string_list = json.dumps(welcome_roles)
    await execute(
        "UPDATE serverconf SET WelcomeRoles = ? WHERE IdServerconf = ?",
        string_list,
        guild_id,
    )


async def get_server_config(guild_id: int) -> dict:
    row = await execute(
        "SELECT * FROM serverconf WHERE IdServerconf = ?", guild_id, fetch="one"
    )
    if not row:
        return {
            "guild_id": guild_id,
            "welcome_channel_id": None,
            "voice_creation_channel_id": None,
            "reaction_toggle": 1,
            "welcome_roles": "[]",
            "react_roles": "[]",
        }
    return {
        "guild_id": row[0],
        "welcome_channel_id": row[1],
        "voice_creation_channel_id": row[2],
        "reaction_toggle": row[3],
        "welcome_roles": row[4],
        "react_roles": row[5],
    }


async def get_user_config(user_id: int) -> dict:
    await create_default_user_config(user_id)
    row = await execute("SELECT * FROM userconf WHERE UserID = ?", user_id, fetch="one")
    if not row:
        return {"ChanName": "None", "Starbits": 0, "StarbitsNextCollect": 0}
    return {
        "ChanName": row[1],
        "Starbits": row[2],
        "StarbitsNextCollect": row[3],
    }


async def get_reactroles(guildid: int) -> list[dict]:
    await create_default_server_config(guildid)
    row = await execute(
        f"SELECT ReactRoles FROM serverconf WHERE IdServerconf = ?",
        guildid,
        fetch=fetchType.fetchone,
    )
    print(row)  # debugging idfk
    return row[0]


async def create_default_user_config(user_id: int) -> None:
    await execute("INSERT INTO userconf (UserID) VALUES (?)", user_id)


async def set_starbits(user_id: int, starbits: int) -> None:
    await create_default_user_config(user_id)
    await execute(
        "UPDATE userconf SET Starbits = ? WHERE UserID = ?",
        starbits,
        user_id,
    )


async def set_starbit_collection(user_id: int, timestamp: int) -> None:
    await create_default_user_config(user_id)
    await execute(
        "UPDATE userconf SET StarbitsNextCollect = ? WHERE UserID = ?",
        timestamp,
        user_id,
    )


async def add_starbits(user_id: int, starbits: int) -> None:
    await create_default_user_config(user_id)
    await execute(
        "UPDATE userconf SET Starbits = Starbits + ? WHERE UserID = ?",
        starbits,
        user_id,
    )


async def set_channel_name(user_id: int, chan_name: str) -> None:
    await create_default_user_config(user_id)
    await execute(
        "UPDATE userconf SET ChanName = ? WHERE UserID = ?",
        chan_name,
        user_id,
    )
