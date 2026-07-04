from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.host import Host
from app.models.host_metric import HostMetric


class MetricRepository:
    def __init__(self, db: Session):
        self.db = db

    def resolve_host_id(self, host_id: int | None, hostname_or_ip: str | None) -> int | None:
        if host_id is not None:
            return host_id if self.db.get(Host, host_id) else None
        if hostname_or_ip:
            host = self.db.scalar(
                select(Host).where(Host.hostname_or_ip == hostname_or_ip)
            )
            return host.id if host else None
        return None

    def add(self, **data) -> HostMetric:
        if data.get("collected_at") is None:
            data["collected_at"] = datetime.now(timezone.utc)
        metric = HostMetric(**data)
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def for_host(self, host_id: int, hours: int = 24, limit: int = 1000) -> list[HostMetric]:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = (
            select(HostMetric)
            .where(HostMetric.host_id == host_id, HostMetric.collected_at >= since)
            .order_by(HostMetric.collected_at.asc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def latest(self, host_id: int) -> HostMetric | None:
        stmt = (
            select(HostMetric)
            .where(HostMetric.host_id == host_id)
            .order_by(HostMetric.collected_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)
