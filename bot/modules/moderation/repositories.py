from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete

from .models import ModerationSettings as Settings
from .models import Warning as Warn


class SettingsRepository:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(session)

    async def get(self, guild_id: int) -> Settings | None:
        return (
            await self.session.execute(
                select(Settings).where(Settings.guild_id == guild_id)
            )
        ).scalar()

    async def save(self, settings: Settings) -> Settings:
        self.session.add(settings)
        await self.session.commit()
        await self.session.refresh(settings)
        return settings

    async def delete(self, settings: Settings) -> None:
        await self.session.delete(settings)
        await self.session.commit()


class WarnRepository:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(session)

    async def save(self, warn: Warn) -> Warn:
        self.session.add(warn)
        await self.session.commit()
        await self.session.refresh(warn)
        return warn

    async def get(self, id: int) -> Warn | None:
        return (await self.session.execute(select(Warn).where(Warn.id == id))).scalar()

    async def delete(self, warn: Warn) -> None:
        await self.session.delete(warn)
        await self.session.commit()

    async def find_by_guild_id(self, guild_id: int) -> Sequence[Warn]:
        return (
            (await self.session.execute(select(Warn).where(Warn.guild_id == guild_id)))
            .scalars()
            .all()
        )

    async def find_by_user_id_and_guild_id(
        self, user_id: int, guild_id: int
    ) -> Sequence[Warn]:
        return (
            (
                await self.session.execute(
                    select(Warn)
                    .where(Warn.user_id == user_id)
                    .where(Warn.guild_id == guild_id)
                )
            )
            .scalars()
            .all()
        )

    async def find_by_moderator_id_and_guild_id(
        self, moderator_id: int, guild_id: int
    ) -> Sequence[Warn]:
        return (
            (
                await self.session.execute(
                    select(Warn)
                    .where(Warn.moderator_id == moderator_id)
                    .where(Warn.guild_id == guild_id)
                )
            )
            .scalars()
            .all()
        )
