from datetime import datetime

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    hosts_total: int
    checks_total: int
    status_counts: dict[str, int]  # OK / WARNING / CRITICAL / UNKNOWN


class IncidentOut(BaseModel):
    alert_id: int
    check_id: int
    check_name: str
    host_id: int
    host_name: str
    status: str
    message: str | None = None
    since: datetime
    acknowledged: bool = False
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None

    class Config:
        from_attributes = True
