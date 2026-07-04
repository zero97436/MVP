from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.crypto import encrypt_config, merge_secret_config
from app.models.check import Check
from app.models.check_result import CheckResult


class CheckRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, host_id: int | None = None) -> list[Check]:
        stmt = select(Check).order_by(Check.name)
        if host_id is not None:
            stmt = stmt.where(Check.host_id == host_id)
        return list(self.db.scalars(stmt))

    def list_active(self) -> list[Check]:
        return list(self.db.scalars(select(Check).where(Check.is_active.is_(True))))

    def get(self, check_id: int) -> Check | None:
        return self.db.get(Check, check_id)

    def create(self, **data) -> Check:
        if "config_json" in data:
            data["config_json"] = encrypt_config(data["config_json"])
        check = Check(**data)
        self.db.add(check)
        self.db.commit()
        self.db.refresh(check)
        return check

    def update(self, check: Check, **data) -> Check:
        if "config_json" in data:
            data["config_json"] = merge_secret_config(data["config_json"], check.config_json)
        for key, value in data.items():
            setattr(check, key, value)
        self.db.commit()
        self.db.refresh(check)
        return check

    def delete(self, check: Check) -> None:
        self.db.delete(check)
        self.db.commit()

    # --- Résultats ---
    def add_result(self, **data) -> CheckResult:
        result = CheckResult(**data)
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result

    def list_results(self, check_id: int, limit: int = 100, offset: int = 0) -> list[CheckResult]:
        stmt = (
            select(CheckResult)
            .where(CheckResult.check_id == check_id)
            .order_by(CheckResult.checked_at.desc())
            .limit(limit)
            .offset(max(0, offset))
        )
        return list(self.db.scalars(stmt))
