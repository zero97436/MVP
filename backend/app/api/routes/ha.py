"""Statut de haute disponibilité (Enterprise) : leader du scheduler, réplicas."""
from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.core.license import require_feature

router = APIRouter(
    prefix="/ha", tags=["ha"],
    dependencies=[Depends(require_admin), Depends(require_feature("ha"))],
)


@router.get("/status")
def ha_status():
    """État du cluster : qui est le scheduler leader, fraîcheur du heartbeat."""
    from app.core.ha import LOCK_TTL_SECONDS, read_leader

    info = read_leader()
    age = info.get("last_heartbeat_age")
    healthy = bool(info.get("current_leader")) and (age is None or age < LOCK_TTL_SECONDS)
    return {
        "healthy": healthy,
        "scheduler_leader": info.get("current_leader"),
        "heartbeat_age_seconds": age,
        "lock_ttl_seconds": LOCK_TTL_SECONDS,
        "redis": info.get("redis", False),
    }
