"""Tâches Celery : exécution d'un check en arrière-plan."""
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.repositories.check_repo import CheckRepository
from app.services.check_service import CheckService
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="run_check")
def run_check_task(check_id: int) -> dict | None:
    """Exécute un check identifié par son id (appelé par le scheduler)."""
    db = SessionLocal()
    try:
        check = CheckRepository(db).get(check_id)
        if not check or not check.is_active:
            return None
        return CheckService(db).run_check(check)
    finally:
        db.close()
