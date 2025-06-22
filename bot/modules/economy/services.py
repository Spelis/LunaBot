from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from .models import EconomyModel
from .repositories import EconomyRepository


class EconomyService:
    def __init__(self, repository: EconomyRepository) -> None:
        self.repository: EconomyRepository = repository

    async def get(self, id: int) -> EconomyModel | None:
        return await self.repository.get(id)

    async def create(self, id: int) -> EconomyModel:
        return await self.repository.save(
            EconomyModel(id=id, balance=0, lastclaim=datetime.fromtimestamp(1))
        )

    async def update(self, u_economy: EconomyModel) -> EconomyModel:
        return await self.repository.save(u_economy)

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(EconomyRepository.from_session(session))
