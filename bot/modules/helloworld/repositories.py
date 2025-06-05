from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from .models import ExampleModel


class ExampleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(session)

    async def get_all(self) -> Sequence:
        """
        Get all ExampleModels from the database.

        Returns:
            list[ExampleModel]: A list of all ExampleModels in the database.
        """
        return (await self.session.execute(select(ExampleModel))).scalars().all()

    async def get(self, id: int) -> ExampleModel | None:
        """
        Get a ExampleModel by its id.

        Args:
            id (int): The id of the ExampleModel to retrieve.

        Returns:
            ExampleModel: The ExampleModel with the given id or None if it doesn't exist.
        """
        return (
            await self.session.execute(
                select(ExampleModel).where(ExampleModel.id == id)
            )
        ).scalar()

    async def delete(self, example: ExampleModel) -> None:
        """
        Delete an instance of ExampleModel from the database.

        Args:
            example (ExampleModel): The instance of ExampleModel to be deleted.

        This function deletes the specified ExampleModel instance from the database
        and commits the change.
        """
        await self.session.delete(example)
        await self.session.commit()

    async def save(self, example: ExampleModel) -> ExampleModel:
        """
        Save an instance of ExampleModel to the database.

        Args:
            example (ExampleModel): The instance of ExampleModel to be saved.

        Returns:
            ExampleModel: The saved instance of ExampleModel with updated state after being committed and refreshed.
        """
        self.session.add(example)
        await self.session.commit()
        await self.session.refresh(example)
        return example
