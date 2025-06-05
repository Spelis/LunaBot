from sqlalchemy.ext.asyncio import AsyncSession

from .models import ExampleModel
from .repositories import ExampleRepository


class ExampleService:
    def __init__(self, repository: ExampleRepository):
        self.repository = repository

    async def get_all(self) -> list[ExampleModel]:
        return list(await self.repository.get_all())

    async def get(self, id: int) -> ExampleModel | None:
        return await self.repository.get(id)

    async def delete(self, example: ExampleModel) -> None:
        return await self.repository.delete(example)

    async def create(self, name: str) -> ExampleModel:
        return await self.repository.save(ExampleModel(name=name))

    async def update(self, example: ExampleModel) -> ExampleModel:
        return await self.repository.save(example)

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(ExampleRepository.from_session(session))
