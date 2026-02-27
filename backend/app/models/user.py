from datetime import datetime

from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    name: str
    email: str = Field(unique=True, index=True)


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    clerk_id: str = Field(unique=True, index=True)
    password_hash: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserRead(SQLModel):
    id: int
    name: str
    email: str
    created_at: datetime
