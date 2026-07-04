"""Scheduler maison : boucle qui planifie l'exécution des checks selon leur intervalle.

Approche MVP simple et robuste : une boucle qui, à intervalle fixe
(SCHEDULER_INTERVAL_SECONDS), regarde quels checks sont "dus" et pousse une tâche
Celery `run_check`. On garde en mémoire le dernier déclenchement par check.

Lancement : python -m app.workers.scheduler
"""
import time
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.repositories.check_repo import CheckRepository
from app.services.downsample_service import DownsampleService
from app.services.retention_service import RetentionService
from app.workers.tasks import run_check_task

logger = get_logger("scheduler")


def run_scheduler() -> None:
    logger.info("Scheduler started (tick=%ss)", settings.SCHEDULER_INTERVAL_SECONDS)
    last_run: dict[int, float] = {}
    last_purge = 0.0
    purge_interval = settings.RETENTION_PURGE_INTERVAL_MINUTES * 60

    while True:
        now = time.time()
        db = SessionLocal()
        try:
            checks = CheckRepository(db).list_active()
            for check in checks:
                # Les checks délégués à un agent-sonde ne sont pas exécutés centralement.
                if check.executor_host_id is not None:
                    continue
                due = now - last_run.get(check.id, 0) >= check.interval_seconds
                if due:
                    last_run[check.id] = now
                    # Délègue au worker Celery (asynchrone).
                    run_check_task.delay(check.id)
                    logger.debug("Dispatched check #%s", check.id)

            # Escalade des alertes non acquittées (à chaque tick).
            from app.services.alert_service import AlertService
            AlertService(db).escalate_pending()

            # Downsampling + purge de rétention périodiques.
            if now - last_purge >= purge_interval:
                last_purge = now
                DownsampleService(db).rollup()  # agrège AVANT de purger le brut
                RetentionService(db).purge()
        except Exception as exc:  # noqa: BLE001
            logger.error("Scheduler loop error: %s", exc)
        finally:
            db.close()

        time.sleep(settings.SCHEDULER_INTERVAL_SECONDS)


if __name__ == "__main__":
    _ = datetime.now(timezone.utc)
    run_scheduler()
