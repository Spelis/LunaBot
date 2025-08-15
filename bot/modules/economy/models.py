from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class EconomyModel(SQLModel, table=True):
    id: int = Field(primary_key=True, unique=True, nullable=False)
    balance: float = Field(default=0)
    last_claim: datetime = Field(
        default_factory=lambda: datetime.fromtimestamp(1, tz=timezone.utc)
    )
    @property
    def utc_last_claim(self):
        return self.last_claim.astimezone(tz=timezone.utc)
