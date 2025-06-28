from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class ModerationSettings(SQLModel, table=True):
    guild_id: int = Field(primary_key=True)
    log_channel: int | None = Field(default=None)


class Infraction(SQLModel):
    id: int = Field(default=None, primary_key=True)
    guild_id: int
    user_id: int
    moderator_id: int
    reason: str
    date: str = Field(default_factory=lambda: str(datetime.now(tz=timezone.utc)))


class Warning(Infraction, table=True):
    pass


class Timeout(Infraction, table=True):
    pass


class Ban(Infraction, table=True):
    pass


class Kick(Infraction, table=True):
    pass
