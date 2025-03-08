import aiosqlite

# credits to HyScript7 for teaching me sqlite

schema_created: bool = False
async def create_schema() -> None:
    async with aiosqlite.connect("servers.db") as conn:
        async with conn.cursor() as c:
            await c.execute(
                """
                CREATE TABLE IF NOT EXISTS serverconf (
                    IdServerconf INTEGER PRIMARY KEY,
                    WelcomeChannelId INTEGER DEFAULT NULL,
                    VoiceCreationId INTEGER DEFAULT NULL
                );
                """,
            )
            await conn.commit()

async def create_default_server_config(guild_id: int) -> None:
    await create_schema()
    async with aiosqlite.connect("servers.db") as conn:
        async with conn.cursor() as c:
            try:
                await c.execute("INSERT INTO serverconf (IdServerconf) VALUES (?)", (guild_id,))
                await conn.commit()
            except aiosqlite.IntegrityError:
                return


async def set_server_welcome_channel(guild_id: int, welcome_channel_id: int) -> None:
    await create_schema()
    await create_default_server_config(guild_id)
    async with aiosqlite.connect("servers.db") as conn:
        async with conn.cursor() as c:
            await c.execute(
                "UPDATE serverconf SET WelcomeChannelId = ? WHERE IdServerconf = ?",
                (welcome_channel_id, guild_id),
            )
            await conn.commit()
            
async def set_server_voice_creation_channel(guild_id: int, voice_creation_channel_id: int) -> None:
    await create_schema()
    await create_default_server_config(guild_id)
    async with aiosqlite.connect("servers.db") as conn:
        async with conn.cursor() as c:
            await c.execute(
                "UPDATE serverconf SET VoiceCreationId = ? WHERE IdServerconf = ?",
                (voice_creation_channel_id, guild_id),
            )
            await conn.commit()


async def get_server_config(guild_id: int) -> dict:
    await create_schema()
    async with aiosqlite.connect("servers.db") as conn:
        async with conn.cursor() as c:
            await c.execute("SELECT * FROM serverconf WHERE IdServerconf = ?", (guild_id,))
            row = await c.fetchone()
            if not row:
                # If there is no such entry in the database
                # Return a mock of the default config
                return {
                    "guild_id": guild_id,
                    "welcome_channel_id": None,
                    "voice_creation_channel_id": None,
                }
            # otherwise
            return {
                "guild_id": row[0],
                "welcome_channel_id": row[1],
                "voice_creation_channel_id": row[2],
            }
