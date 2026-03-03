from datetime import datetime, UTC
from typing import Optional
from sqlmodel import Field, SQLModel


class WaitlistEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WaitlistCreate(SQLModel):
    name: str
    email: str


class WaitlistRead(SQLModel):
    id: int
    name: str
    email: str
    created_at: datetime
