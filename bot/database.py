import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from .config import settings
from .logs import get_logger

get_logger("sqlalchemy", level=logging.WARNING)

engine: AsyncEngine = create_async_engine(
    settings.database_uri, echo=False, future=True
)


async def init_db():
    """
    Initializes the database by creating all tables and other database constructs defined
    by the SQLModel metadata.

    This function is idempotent, so it is safe to call multiple times. It will only
    create the tables and other database constructs if they do not already exist.

    This function should be called once when the application starts up, and ideally should
    be called from the application's startup event handler.

    This function is a coroutine and should be called with `await`.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_db():
    """
    Drops all tables and other database constructs defined by the SQLModel metadata.

    This function should be used with caution, as it will permanently delete all data
    in the database.

    This function is idempotent, so it is safe to call multiple times. It will only
    drop the tables and other database constructs if they exist.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Asynchronously yields a database session for performing database operations.

    This function initializes an asynchronous session using the configured
    database engine. It yields a session that can be used to execute database
    commands. After yielding, it ensures the session is rolled back to maintain
    a clean state. This is useful for situations where you want to perform
    database operations without persisting changes.

    Yields:
        AsyncSession: An asynchronous SQLAlchemy session object.

    Example:
        with async_session() as session:
            ... # Use the session for database operations
    """

    async_session: sessionmaker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore
    async with async_session() as session:
        session: AsyncSession
        try:
            yield session
        finally:
            await session.rollback()
