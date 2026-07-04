"""Agrégations pour le dashboard."""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.check import Check
from app.models.enums import CheckStatus
from app.models.host import Host


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def summary(self) -> dict:
        hosts_total = self.db.scalar(select(func.count(Host.id))) or 0
        checks_total = self.db.scalar(select(func.count(Check.id))) or 0

        counts = {s.value: 0 for s in CheckStatus}
        rows = self.db.execute(
            select(Check.last_status, func.count(Check.id)).group_by(Check.last_status)
        ).all()
        for status, count in rows:
            key = status or CheckStatus.UNKNOWN.value
            counts[key] = counts.get(key, 0) + count

        return {
            "hosts_total": hosts_total,
            "checks_total": checks_total,
            "status_counts": counts,
        }

    def incidents(self) -> list[dict]:
        stmt = (
            select(Alert, Check, Host)
            .join(Check, Alert.check_id == Check.id)
            .join(Host, Check.host_id == Host.id)
            .where(Alert.is_active.is_(True))
            .order_by(Alert.created_at.desc())
        )
        out = []
        for alert, check, host in self.db.execute(stmt).all():
            out.append(
                {
                    "alert_id": alert.id,
                    "check_id": check.id,
                    "check_name": check.name,
                    "host_id": host.id,
                    "host_name": host.name,
                    "status": alert.status,
                    "message": alert.message,
                    "since": alert.created_at,
                    "acknowledged": alert.acknowledged,
                    "acknowledged_by": alert.acknowledged_by,
                    "acknowledged_at": alert.acknowledged_at,
                }
            )
        return out

    def acknowledge(self, alert_id: int, user_email: str, ack: bool = True) -> Alert | None:
        alert = self.db.get(Alert, alert_id)
        if not alert:
            return None
        alert.acknowledged = ack
        alert.acknowledged_by = user_email if ack else None
        alert.acknowledged_at = datetime.now(timezone.utc) if ack else None
        self.db.commit()
        self.db.refresh(alert)

        from app.services.event_service import EventService

        check = self.db.get(Check, alert.check_id)
        EventService(self.db).record(
            "alert_acknowledged" if ack else "alert_unacknowledged",
            f"Incident {'acquitté' if ack else 'ré-ouvert'} par {user_email}",
            host_id=check.host_id if check else None,
            check_id=alert.check_id,
            actor=user_email,
        )
        return alert
