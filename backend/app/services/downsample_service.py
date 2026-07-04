"""Downsampling : agrège les échantillons bruts host_metrics en moyennes horaires.

Idempotent : recalcule une fenêtre récente (ROLLUP_WINDOW_HOURS) à chaque passage,
ce qui capture les arrivées tardives sans toucher aux anciens rollups (dont les
données brutes ont pu être purgées). Calcul fait en Python pour rester portable
(Postgres en prod, SQLite en test).
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.host_metric import HostMetric
from app.models.host_metric_hourly import HostMetricHourly

logger = get_logger(__name__)

ROLLUP_WINDOW_HOURS = 48


def _hour_floor(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def _avg(vals: list[float]) -> float | None:
    return round(sum(vals) / len(vals), 2) if vals else None


def _max(vals: list[float]) -> float | None:
    return round(max(vals), 2) if vals else None


class DownsampleService:
    def __init__(self, db: Session):
        self.db = db

    def rollup(self) -> int:
        """Recalcule les rollups horaires sur la fenêtre récente. Renvoie le nb de
        buckets (hôte×heure) écrits."""
        window_start = _hour_floor(datetime.now(timezone.utc) - timedelta(hours=ROLLUP_WINDOW_HOURS))

        rows = self.db.scalars(
            select(HostMetric).where(HostMetric.collected_at >= window_start)
        ).all()
        if not rows:
            return 0

        # Regroupe (host_id, heure) -> listes de valeurs.
        groups: dict[tuple[int, datetime], dict[str, list[float]]] = {}
        for m in rows:
            key = (m.host_id, _hour_floor(m.collected_at))
            g = groups.setdefault(key, {"cpu": [], "mem": [], "disk": [], "net": []})
            if m.cpu_percent is not None:
                g["cpu"].append(m.cpu_percent)
            if m.mem_percent is not None:
                g["mem"].append(m.mem_percent)
            if m.disk_percent is not None:
                g["disk"].append(m.disk_percent)
            if m.net_mbps is not None:
                g["net"].append(m.net_mbps)

        # Remplace les rollups de la fenêtre (idempotent), conserve les plus anciens.
        self.db.execute(delete(HostMetricHourly).where(HostMetricHourly.bucket >= window_start))

        written = 0
        for (host_id, bucket), g in groups.items():
            count = max(len(g["cpu"]), len(g["mem"]), len(g["disk"]), len(g["net"]))
            self.db.add(
                HostMetricHourly(
                    host_id=host_id,
                    bucket=bucket,
                    cpu_avg=_avg(g["cpu"]), cpu_max=_max(g["cpu"]),
                    mem_avg=_avg(g["mem"]), mem_max=_max(g["mem"]),
                    disk_avg=_avg(g["disk"]), disk_max=_max(g["disk"]),
                    net_avg=_avg(g["net"]), net_max=_max(g["net"]),
                    sample_count=count,
                )
            )
            written += 1

        self.db.commit()
        if written:
            logger.info("Downsample wrote %d hourly buckets", written)
        return written

    def for_host(self, host_id: int, days: int = 30) -> list[HostMetricHourly]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(HostMetricHourly)
            .where(HostMetricHourly.host_id == host_id, HostMetricHourly.bucket >= since)
            .order_by(HostMetricHourly.bucket.asc())
        )
        return list(self.db.scalars(stmt))
