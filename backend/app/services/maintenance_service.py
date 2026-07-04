"""Fenêtres de maintenance : création/lecture + détection « check en maintenance »."""
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.check import Check
from app.models.maintenance import MaintenanceWindow


class MaintenanceService:
    def __init__(self, db: Session):
        self.db = db

    def is_in_maintenance(self, check: Check) -> bool:
        """Vrai si une fenêtre active couvre ce check (lui-même, son hôte, ou globale)."""
        now = datetime.now(timezone.utc)
        stmt = select(MaintenanceWindow.id).where(
            MaintenanceWindow.starts_at <= now,
            MaintenanceWindow.ends_at >= now,
            or_(
                MaintenanceWindow.check_id == check.id,
                MaintenanceWindow.host_id == check.host_id,
                (MaintenanceWindow.host_id.is_(None)) & (MaintenanceWindow.check_id.is_(None)),
            ),
        )
        return self.db.scalar(stmt) is not None

    def list(self) -> list[MaintenanceWindow]:
        return list(
            self.db.scalars(select(MaintenanceWindow).order_by(MaintenanceWindow.ends_at.desc()))
        )

    def create(self, **data) -> MaintenanceWindow:
        mw = MaintenanceWindow(**data)
        self.db.add(mw)
        self.db.commit()
        self.db.refresh(mw)
        return mw

    def delete(self, mw_id: int) -> bool:
        mw = self.db.get(MaintenanceWindow, mw_id)
        if not mw:
            return False
        self.db.delete(mw)
        self.db.commit()
        return True
