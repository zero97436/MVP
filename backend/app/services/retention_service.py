"""Rétention des données : purge des lignes anciennes pour borner la taille de la base.

Tables concernées (les plus volumineuses) :
  - check_results   : résultats horodatés des sondes
  - host_metrics    : échantillons CPU/RAM/disque/réseau poussés par les agents
  - alerts          : alertes RÉSOLUES (inactives) anciennes — on garde les actives

Les fenêtres sont configurables (settings.RETENTION_*). La purge supprime par lot
via DELETE ... WHERE date < seuil.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings

# Plafonds Community (la rétention ÉTENDUE est une feature Professional).
_DEFAULT_RETENTION = {
    "RETENTION_CHECK_RESULTS_DAYS": 30,
    "RETENTION_HOST_METRICS_DAYS": 15,
    "RETENTION_HOST_METRICS_HOURLY_DAYS": 365,
    "RETENTION_RESOLVED_ALERTS_DAYS": 90,
    "RETENTION_EVENTS_DAYS": 90,
}


def retention_days(key: str) -> int:
    """Valeur effective : configurable librement avec la feature
    « extended_retention », sinon plafonnée aux valeurs par défaut."""
    from app.core.license import has_feature

    configured = getattr(settings, key)
    if has_feature("extended_retention"):
        return configured
    return min(configured, _DEFAULT_RETENTION[key])
from app.core.logging import get_logger
from app.models.alert import Alert
from app.models.check_result import CheckResult
from app.models.event_log import EventLog
from app.models.host_metric import HostMetric
from app.models.host_metric_hourly import HostMetricHourly

logger = get_logger(__name__)


class RetentionService:
    def __init__(self, db: Session):
        self.db = db

    def purge(self) -> dict[str, int]:
        """Supprime les données au-delà des fenêtres configurées. Renvoie le nb de lignes
        supprimées par table."""
        now = datetime.now(timezone.utc)
        deleted: dict[str, int] = {}

        deleted["check_results"] = self._purge_before(
            CheckResult,
            CheckResult.checked_at,
            now - timedelta(days=retention_days("RETENTION_CHECK_RESULTS_DAYS")),
        )
        deleted["host_metrics"] = self._purge_before(
            HostMetric,
            HostMetric.collected_at,
            now - timedelta(days=retention_days("RETENTION_HOST_METRICS_DAYS")),
        )
        deleted["host_metrics_hourly"] = self._purge_before(
            HostMetricHourly,
            HostMetricHourly.bucket,
            now - timedelta(days=retention_days("RETENTION_HOST_METRICS_HOURLY_DAYS")),
        )
        # Alertes : seulement celles résolues (inactives) et anciennes.
        cutoff_alerts = now - timedelta(days=retention_days("RETENTION_RESOLVED_ALERTS_DAYS"))
        stmt = delete(Alert).where(
            Alert.is_active.is_(False), Alert.created_at < cutoff_alerts
        )
        deleted["alerts"] = self.db.execute(stmt).rowcount or 0

        deleted["events"] = self._purge_before(
            EventLog, EventLog.created_at,
            now - timedelta(days=retention_days("RETENTION_EVENTS_DAYS")),
        )

        self.db.commit()
        total = sum(deleted.values())
        if total:
            logger.info("Retention purge removed %d rows: %s", total, deleted)
        return deleted

    def _purge_before(self, model, column, cutoff: datetime) -> int:
        result = self.db.execute(delete(model).where(column < cutoff))
        return result.rowcount or 0

    def stats(self) -> dict:
        """Compteurs et plus ancienne entrée par table (pour l'UI maintenance)."""
        return {
            "check_results": self._table_stats(CheckResult, CheckResult.checked_at),
            "host_metrics": self._table_stats(HostMetric, HostMetric.collected_at),
            "host_metrics_hourly": self._table_stats(HostMetricHourly, HostMetricHourly.bucket),
            "alerts": self._table_stats(Alert, Alert.created_at),
            "events": self._table_stats(EventLog, EventLog.created_at),
            "retention_days": {
                "check_results": retention_days("RETENTION_CHECK_RESULTS_DAYS"),
                "host_metrics": retention_days("RETENTION_HOST_METRICS_DAYS"),
                "host_metrics_hourly": retention_days("RETENTION_HOST_METRICS_HOURLY_DAYS"),
                "resolved_alerts": retention_days("RETENTION_RESOLVED_ALERTS_DAYS"),
                "events": retention_days("RETENTION_EVENTS_DAYS"),
            },
        }

    def _table_stats(self, model, column) -> dict:
        count = self.db.scalar(select(func.count(model.id))) or 0
        oldest = self.db.scalar(select(func.min(column)))
        return {"count": count, "oldest": oldest.isoformat() if oldest else None}
