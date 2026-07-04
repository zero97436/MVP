from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CheckResultOut(BaseModel):
    id: int
    check_id: int
    status: str
    value: float | None = None
    message: str | None = None
    perfdata: dict[str, Any] = {}
    duration_ms: int | None = None
    checked_at: datetime

    class Config:
        from_attributes = True
