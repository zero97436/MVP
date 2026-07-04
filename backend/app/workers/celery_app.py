"""Instance Celery."""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "supervision",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

# Import des tâches pour qu'elles soient enregistrées.
celery_app.autodiscover_tasks(["app.workers"])
import app.workers.tasks  # noqa: E402,F401
