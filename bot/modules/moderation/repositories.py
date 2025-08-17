from typing import TypeVar
from abc import ABC
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from .models import ModerationSettings as Settings
from . import models


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

T = TypeVar("T", bound=models.Infraction)

class AbstractionInfractionRepository[T](ABC):
    model: type
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(session)

    async def save(self, infraction: T) -> T:
        self.session.add(infraction)
        await self.session.commit()
        await self.session.refresh(infraction)
        return infraction

    async def get(self, id: int) -> T | None:
        return (await self.session.execute(select(self.model).where(self.model.id == id))).scalar()

    async def delete(self, infraction: T) -> None:
        await self.session.delete(infraction)
        await self.session.commit()

    async def find_by_guild_id(self, guild_id: int) -> Sequence[T]:
        return (
            (await self.session.execute(select(self.model).where(self.model.guild_id == guild_id)))
            .scalars()
            .all()
        )

    async def find_by_user_id_and_guild_id(
        self, user_id: int, guild_id: int
    ) -> Sequence[T]:
        return (
            (
                await self.session.execute(
                    select(self.model)
                    .where(self.model.user_id == user_id)
                    .where(self.model.guild_id == guild_id)
                )
            )
            .scalars()
            .all()
        )

    async def find_by_moderator_id_and_guild_id(
        self, moderator_id: int, guild_id: int
    ) -> Sequence[T]:
        return (
            (
                await self.session.execute(
                    select(self.model)
                    .where(self.model.moderator_id == moderator_id)
                    .where(self.model.guild_id == guild_id)
                )
            )
            .scalars()
            .all()
        )


class WarnRepository(AbstractionInfractionRepository[models.Warn]):
    model = models.Warn

    def __init__(self, session: AsyncSession):
        super().__init__(session)


class TimeoutRepository(AbstractionInfractionRepository[models.Timeout]):
    model = models.Timeout

    def __init__(self, session: AsyncSession):
        super().__init__(session)

class BanRepository(AbstractionInfractionRepository[models.Ban]):
    model = models.Ban

    def __init__(self, session: AsyncSession):    
        super().__init__(session)


class KickRepository(AbstractionInfractionRepository[models.Kick]):
    model = models.Kick

    def __init__(self, session: AsyncSession):    
        super().__init__(session)
