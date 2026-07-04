"""Auto-surveillance : santé des composants internes (DB, Redis, workers, scheduler)."""
import time
from datetime import datetime, timezone

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.check import Check
from app.models.check_result import CheckResult


class SystemHealthService:
    def __init__(self, db: Session):
        self.db = db

    def health(self) -> dict:
        components = {
            "database": self._db(),
            "redis": self._redis(),
            "celery_workers": self._celery(),
            "scheduler": self._scheduler(),
        }
        ok = all(c["ok"] for c in components.values())
        return {"status": "ok" if ok else "degraded", "components": components}

    def _db(self) -> dict:
        t0 = time.time()
        try:
            self.db.execute(text("SELECT 1"))
            return {"ok": True, "latency_ms": int((time.time() - t0) * 1000)}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)[:120]}

    def _redis(self) -> dict:
        try:
            import redis

            r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1)
            r.ping()
            return {"ok": True}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)[:120]}

    def _celery(self) -> dict:
        try:
            from app.workers.celery_app import celery_app

            replies = celery_app.control.ping(timeout=1) or []
            count = len(replies)
            return {"ok": count > 0, "count": count}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "count": 0, "error": str(exc)[:120]}

    def _scheduler(self) -> dict:
        """Heuristique : si des checks centraux actifs existent, un résultat récent
        prouve que scheduler + worker tournent."""
        active = self.db.scalar(
            select(func.count(Check.id)).where(
                Check.is_active.is_(True), Check.executor_host_id.is_(None)
            )
        ) or 0
        last = self.db.scalar(select(func.max(CheckResult.checked_at)))
        if not active:
            return {"ok": True, "active_checks": 0, "last_result_age_seconds": None}
        if last is None:
            return {"ok": False, "active_checks": active, "last_result_age_seconds": None}
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        age = int((datetime.now(timezone.utc) - last).total_seconds())
        # Tolérance large : OK si un résultat dans les 10 dernières minutes.
        return {"ok": age < 600, "active_checks": active, "last_result_age_seconds": age}
