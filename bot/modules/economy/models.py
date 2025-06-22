from datetime import datetime

from sqlmodel import Field, SQLModel


class EconomyModel(SQLModel, table=True):
    id: int = Field(primary_key=True, unique=True, nullable=False)
    balance: int
    lastclaim: datetime
