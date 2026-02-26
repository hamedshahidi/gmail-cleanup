from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AccountMessage(BaseModel):
    id: str
    subject: str
    from_: str = Field(
        validation_alias="from",
        serialization_alias="from",
    )
    snippet: str
    date: datetime
    model_config = ConfigDict(populate_by_name=True)
