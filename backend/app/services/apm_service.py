"""APM applicatif : agrégation des échantillons poussés par les applications.

KPIs par application : débit (req/min), taux d'erreur (%), latence moyenne (ms),
calculés sur une fenêtre glissante, + séries temporelles par buckets.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.apm_sample import ApmSample


class ApmService:
    def __init__(self, db: Session):
        self.db = db

    def ingest(
        self,
        app_name: str,
        requests: int,
        errors: int = 0,
        latency_ms: float | None = None,
        environment: str = "prod",
        collected_at: datetime | None = None,
    ) -> ApmSample:
        sample = ApmSample(
            app_name=app_name[:128], environment=environment[:64],
            requests=max(0, requests), errors=max(0, errors), latency_ms=latency_ms,
            collected_at=collected_at or datetime.now(timezone.utc),
        )
        self.db.add(sample)
        self.db.commit()
        self.db.refresh(sample)
        return sample

    def window_stats(self, app_name: str, minutes: int = 15) -> dict:
        """KPIs agrégés d'une application sur la fenêtre glissante."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        row = self.db.execute(
            select(
                func.coalesce(func.sum(ApmSample.requests), 0),
                func.coalesce(func.sum(ApmSample.errors), 0),
                func.avg(ApmSample.latency_ms),
                func.max(ApmSample.collected_at),
            ).where(ApmSample.app_name == app_name, ApmSample.collected_at >= cutoff)
        ).one()
        requests, errors, latency, last_seen = row
        error_rate = round(errors / requests * 100, 2) if requests else 0.0
        return {
            "app_name": app_name,
            "window_minutes": minutes,
            "requests": int(requests),
            "errors": int(errors),
            "error_rate": error_rate,
            "rpm": round(requests / minutes, 2) if minutes else 0.0,
            "latency_ms": round(latency, 1) if latency is not None else None,
            "last_seen": last_seen.isoformat() if last_seen else None,
        }

    def apps(self, minutes: int = 15) -> list[dict]:
        """Liste des applications connues avec leurs KPIs (fenêtre glissante)."""
        names = self.db.scalars(
            select(ApmSample.app_name).distinct().order_by(ApmSample.app_name)
        ).all()
        return [self.window_stats(n, minutes) for n in names]

    def series(self, app_name: str, hours: int = 24, buckets: int = 48) -> list[dict]:
        """Série temporelle par buckets : rpm, taux d'erreur, latence."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=hours)
        samples = list(self.db.scalars(
            select(ApmSample)
            .where(ApmSample.app_name == app_name, ApmSample.collected_at >= start)
            .order_by(ApmSample.collected_at)
        ))
        width = (now - start) / buckets
        out = []
        for i in range(buckets):
            b_start = start + i * width
            b_end = b_start + width
            chunk = [
                s for s in samples
                if b_start <= (s.collected_at if s.collected_at.tzinfo else s.collected_at.replace(tzinfo=timezone.utc)) < b_end
            ]
            req = sum(s.requests for s in chunk)
            err = sum(s.errors for s in chunk)
            lat = [s.latency_ms for s in chunk if s.latency_ms is not None]
            out.append({
                "t": b_start.isoformat(),
                "rpm": round(req / (width.total_seconds() / 60), 2) if req else 0.0,
                "error_rate": round(err / req * 100, 2) if req else 0.0,
                "latency_ms": round(sum(lat) / len(lat), 1) if lat else None,
            })
        return out
