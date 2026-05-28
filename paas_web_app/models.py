from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, String, func
from sqlmodel import Field, SQLModel


class LinkBase(SQLModel):
    original_url: str
    short_name: str = Field(sa_column=Column(String, unique=True, nullable=False))


class Link(LinkBase, table=True):
    __tablename__ = "links"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )


class LinkCreate(LinkBase):
    pass


class LinkRead(LinkBase):
    id: int
    short_url: str

