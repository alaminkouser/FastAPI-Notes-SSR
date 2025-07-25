from datetime import datetime
from typing import Optional
from sqlmodel import Column, DateTime, Field, SQLModel, func

class Notes(SQLModel, table=True):
    uid: int | None = Field(default=None, primary_key=True)
    user_uid: str = Field(nullable=False)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), nullable=True
        )
    )
    note: str = Field(nullable=False)
