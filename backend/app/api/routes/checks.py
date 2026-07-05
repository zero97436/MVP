from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_operator
from app.core.license import has_feature
from app.core.tenancy import host_visible, is_scoped, visible_host_ids
from app.db.session import get_db
from app.models.user import User
from app.repositories.check_repo import CheckRepository
from app.repositories.host_repo import HostRepository
from app.schemas.check import CheckCreate, CheckOut, CheckUpdate
from app.schemas.result import CheckResultOut
from app.services.check_service import CheckService

router = APIRouter(prefix="/checks", tags=["checks"], dependencies=[Depends(get_current_user)])


def _check_seen(db: Session, user: User, check):
    """404 si le check n'existe pas ou si son hôte n'est pas visible par l'utilisateur."""
    if not check:
        raise HTTPException(404, "Check not found")
    if is_scoped(user) and not host_visible(user, HostRepository(db).get(check.host_id)):
        raise HTTPException(404, "Check not found")
    return check


@router.get("", response_model=list[CheckOut])
def list_checks(host_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    checks = CheckRepository(db).list(host_id=host_id)
    allowed = visible_host_ids(db, user)
    if allowed is not None:
        checks = [c for c in checks if c.host_id in allowed]
    return checks


@router.post("", response_model=CheckOut, status_code=201, dependencies=[Depends(require_operator)])
def create_check(payload: CheckCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    host = HostRepository(db).get(payload.host_id)
    if not host:
        raise HTTPException(400, "host_id does not exist")
    if not host_visible(user, host):
        raise HTTPException(404, "Host not found")
    if payload.executor_host_id and not has_feature("distributed"):
        raise HTTPException(403, "Supervision distribuée (sondes) disponible à partir du plan Business.")
    data = payload.model_dump()
    data["type"] = data["type"].value if hasattr(data["type"], "value") else data["type"]
    return CheckRepository(db).create(**data)


@router.get("/{check_id}", response_model=CheckOut)
def get_check(check_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _check_seen(db, user, CheckRepository(db).get(check_id))


@router.put("/{check_id}", response_model=CheckOut, dependencies=[Depends(require_operator)])
def update_check(check_id: int, payload: CheckUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    repo = CheckRepository(db)
    check = _check_seen(db, user, repo.get(check_id))
    data = payload.model_dump(exclude_unset=True)
    if "type" in data and hasattr(data["type"], "value"):
        data["type"] = data["type"].value
    return repo.update(check, **data)


@router.delete("/{check_id}", status_code=204, dependencies=[Depends(require_operator)])
def delete_check(check_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    repo = CheckRepository(db)
    check = _check_seen(db, user, repo.get(check_id))
    repo.delete(check)


@router.post("/{check_id}/run", dependencies=[Depends(require_operator)])
def run_check_now(check_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _check_seen(db, user, CheckRepository(db).get(check_id))
    result = CheckService(db).run_check_by_id(check_id)
    if result is None:
        raise HTTPException(404, "Check not found")
    return result


@router.get("/{check_id}/results", response_model=list[CheckResultOut])
def list_results(check_id: int, limit: int = 100, offset: int = 0, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _check_seen(db, user, CheckRepository(db).get(check_id))
    return CheckRepository(db).list_results(check_id, limit=limit, offset=offset)
