from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.services.downsample_service import DownsampleService
from app.services.retention_service import RetentionService
from app.services.system_health_service import SystemHealthService

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/system")
def system_health(db: Session = Depends(get_db)):
    """Auto-surveillance : santé DB / Redis / workers Celery / scheduler."""
    return SystemHealthService(db).health()


@router.get("/stats")
def db_stats(db: Session = Depends(get_db)):
    """Volumétrie des tables historisées + fenêtres de rétention."""
    return RetentionService(db).stats()


@router.post("/retention/run")
def run_retention(db: Session = Depends(get_db)):
    """Déclenche immédiatement la purge de rétention."""
    deleted = RetentionService(db).purge()
    return {"deleted": deleted, "total": sum(deleted.values())}


@router.post("/rollup/run")
def run_rollup(db: Session = Depends(get_db)):
    """Déclenche immédiatement le downsampling (agrégation horaire)."""
    written = DownsampleService(db).rollup()
    return {"buckets_written": written}
