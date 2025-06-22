from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from .models import EconomyModel


class EconomyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get(self, id: int) -> EconomyModel | None:
        """
        Get a users Starbit balance.

        Args:
            id (int): The user's ID

        Returns:
            int: The balance the user currently has, or zero if None.
        """
        result = (
            await self.session.execute(
                select(EconomyModel).where(EconomyModel.id == id)
            )
        ).one_or_none()
        return result[0] if result else None

    async def save(self, u_economy: EconomyModel) -> EconomyModel:
        """
        Save an instance of EconomyModel to the database.

        Args:
            u_economy (EconomyModel): The User's Economy object.

        Returns:
            EconomyModel: The saved instance
        """
        self.session.add(u_economy)
        await self.session.commit()
        await self.session.refresh(u_economy)
        return u_economy

    @classmethod
    def from_session(cls, session: AsyncSession):
        return cls(session)
