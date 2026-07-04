from datetime import datetime

from pydantic import BaseModel


class MaintenanceCreate(BaseModel):
    host_id: int | None = None
    check_id: int | None = None
    reason: str | None = None
    starts_at: datetime
    ends_at: datetime


class MaintenanceOut(BaseModel):
    id: int
    host_id: int | None = None
    check_id: int | None = None
    reason: str | None = None
    starts_at: datetime
    ends_at: datetime
    created_by: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
