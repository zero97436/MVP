from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_operator
from app.db.session import get_db
from app.models.user import User
from app.schemas.maintenance import MaintenanceCreate, MaintenanceOut
from app.services.event_service import EventService
from app.services.maintenance_service import MaintenanceService

router = APIRouter(
    prefix="/maintenances", tags=["maintenances"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=list[MaintenanceOut])
def list_maintenances(db: Session = Depends(get_db)):
    return MaintenanceService(db).list()


@router.post("", response_model=MaintenanceOut, status_code=201)
def create_maintenance(
    payload: MaintenanceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    if payload.ends_at <= payload.starts_at:
        raise HTTPException(400, "La fin doit être après le début")
    mw = MaintenanceService(db).create(
        host_id=payload.host_id,
        check_id=payload.check_id,
        reason=payload.reason,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        created_by=user.email,
    )
    scope = f"hôte #{mw.host_id}" if mw.host_id else ("check #" + str(mw.check_id) if mw.check_id else "global")
    EventService(db).record(
        "maintenance_created", f"Maintenance planifiée ({scope}) — {mw.reason or ''}".strip(),
        host_id=mw.host_id, check_id=mw.check_id, actor=user.email,
    )
    return mw


@router.delete("/{mw_id}", status_code=204)
def delete_maintenance(
    mw_id: int, db: Session = Depends(get_db), user: User = Depends(require_operator)
):
    if not MaintenanceService(db).delete(mw_id):
        raise HTTPException(404, "Maintenance introuvable")
    EventService(db).record("maintenance_deleted", f"Maintenance #{mw_id} supprimée", actor=user.email)
