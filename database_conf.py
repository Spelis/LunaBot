import aiosqlite

# credits to HyScript7 for teaching me sqlite

FILE = "database.db"

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
                    ReactionToggle INTEGER DEFAULT 1
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
            await conn.commit()
            
async def execute(query: str, *args) -> None:
    async with aiosqlite.connect(FILE) as conn:
        async with conn.cursor() as c:
            await c.execute(query, args)
            await conn.commit()
            return await c.fetchall()

async def create_default_server_config(guild_id: int) -> None:
    await create_schema()
    async with aiosqlite.connect(FILE) as conn:
        async with conn.cursor() as c:
            try:
                await c.execute("INSERT INTO serverconf (IdServerconf) VALUES (?)", (guild_id,))
                await conn.commit()
            except aiosqlite.IntegrityError:
                return


async def set_server_welcome_channel(guild_id: int, welcome_channel_id: int) -> None:
    await create_schema()
    await create_default_server_config(guild_id)
    async with aiosqlite.connect(FILE) as conn:
        async with conn.cursor() as c:
            await c.execute(
                "UPDATE serverconf SET WelcomeChannelId = ? WHERE IdServerconf = ?",
                (welcome_channel_id, guild_id),
            )
            await conn.commit()
            
async def set_server_voice_creation_channel(guild_id: int, voice_creation_channel_id: int) -> None:
    await create_schema()
    await create_default_server_config(guild_id)
    async with aiosqlite.connect(FILE) as conn:
        async with conn.cursor() as c:
            await c.execute(
                "UPDATE serverconf SET VoiceCreationId = ? WHERE IdServerconf = ?",
                (voice_creation_channel_id, guild_id),
            )
            await conn.commit()
            
async def set_server_reaction_toggle(guild_id: int, reaction_toggle: int) -> None:
    await create_schema()
    await create_default_server_config(guild_id)
    async with aiosqlite.connect(FILE) as conn:
        async with conn.cursor() as c:
            await c.execute(
                "UPDATE serverconf SET ReactionToggle = ? WHERE IdServerconf = ?",
                (reaction_toggle, guild_id),
            )
            await conn.commit()


async def get_server_config(guild_id: int) -> dict:
    await create_schema()
    async with aiosqlite.connect(FILE) as conn:
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
                    "reaction_toggle": 1,
                }
            # otherwise
            return {
                "guild_id": row[0],
                "welcome_channel_id": row[1],
                "voice_creation_channel_id": row[2],
                "reaction_toggle": row[3],
            }
            
async def get_user_config(user_id: int) -> dict:
    await create_schema()
    await create_default_user_config(user_id)
    async with aiosqlite.connect(FILE) as conn:
        async with conn.cursor() as c:
            await c.execute(
                "SELECT * FROM userconf WHERE UserID = (?)", (user_id,)
            )
            row = await c.fetchone()
            if row is None:
                return {"ChanName": "None", "Starbits": 0, "StarbitsNextCollect": 0}
            return {
                "ChanName": row[1],
                "Starbits": row[2],
                "StarbitsNextCollect": row[3],
            }
            
async def create_default_user_config(user_id: int) -> None:
    await create_schema()
    async with aiosqlite.connect(FILE) as conn:
        async with conn.cursor() as c:
            try:
                await c.execute(
                    "INSERT INTO userconf (UserID) VALUES (?)", (user_id,)
                )
                await conn.commit()
            except aiosqlite.IntegrityError:
                return
            
async def set_starbits(user_id: int, starbits: int) -> None: # not currently used but whatever
    await create_schema()
    await create_default_user_config(user_id)
    async with aiosqlite.connect(FILE) as conn:
        async with conn.cursor() as c:
            await c.execute(
                "UPDATE userconf SET Starbits = (?) WHERE UserID = (?)",
                (starbits, user_id),
            )
            await conn.commit()
            
async def set_starbit_collection(user_id: int, timestamp: int) -> None:
    await create_schema()
    await create_default_user_config(user_id)
    async with aiosqlite.connect(FILE) as conn:
        async with conn.cursor() as c:
            await c.execute(
                "UPDATE userconf SET StarbitsNextCollect = (?) WHERE UserID = (?)",
                (timestamp, user_id),
            )
            await conn.commit()

async def add_starbits(user_id: int, starbits: int) -> None:
    await create_schema()
    await create_default_user_config(user_id)
    async with aiosqlite.connect(FILE) as conn:
        async with conn.cursor() as c:
            await c.execute(
                "UPDATE userconf SET Starbits = Starbits + (?) WHERE UserID = (?)",
                (starbits, user_id),
            )
            await conn.commit()
            
async def set_channel_name(user_id: int, chan_name: str) -> None:
    await create_schema()
    await create_default_user_config(user_id)
    async with aiosqlite.connect(FILE) as conn:
        async with conn.cursor() as c:
            await c.execute(
                "UPDATE userconf SET ChanName = (?) WHERE UserID = (?)",
                (chan_name, user_id),
            )
            await conn.commit()
