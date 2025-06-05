from sqlmodel import SQLModel, Field

class ExampleModel(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
