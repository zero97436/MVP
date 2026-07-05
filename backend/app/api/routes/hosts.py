from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_operator
from app.core.license import get_license
from app.db.session import get_db
from app.models.host import Host
from app.repositories.host_repo import HostRepository
from app.schemas.host import HostCreate, HostOut, HostUpdate

router = APIRouter(prefix="/hosts", tags=["hosts"], dependencies=[Depends(get_current_user)])


def enforce_host_limit(db: Session, adding: int = 1) -> None:
    """Bloque la création au-delà du plafond d'hôtes SI la licence en fixe un.

    Édition Community : aucun plafond (max_hosts = None). Un plafond n'existe
    que si une clé de licence en définit un explicitement (accords OEM)."""
    lic = get_license()
    if lic["max_hosts"] is None:
        return
    current = db.query(Host).count()
    if current + adding > lic["max_hosts"]:
        raise HTTPException(
            403,
            f"Limite de la licence atteinte : {current}/{lic['max_hosts']} hôtes "
            f"(plan {lic['plan']}). Contactez l'éditeur pour étendre la licence.",
        )


@router.get("", response_model=list[HostOut])
def list_hosts(db: Session = Depends(get_db)):
    return HostRepository(db).list()


@router.get("/license")
def license_info(db: Session = Depends(get_db)):
    """Plan de licence + quota d'hôtes utilisé (affiché dans l'UI)."""
    lic = get_license()
    return {**lic, "used": db.query(Host).count()}


@router.post("", response_model=HostOut, status_code=201, dependencies=[Depends(require_operator)])
def create_host(payload: HostCreate, db: Session = Depends(get_db)):
    enforce_host_limit(db)
    return HostRepository(db).create(**payload.model_dump())


@router.get("/{host_id}", response_model=HostOut)
def get_host(host_id: int, db: Session = Depends(get_db)):
    host = HostRepository(db).get(host_id)
    if not host:
        raise HTTPException(404, "Host not found")
    return host


@router.put("/{host_id}", response_model=HostOut, dependencies=[Depends(require_operator)])
def update_host(host_id: int, payload: HostUpdate, db: Session = Depends(get_db)):
    repo = HostRepository(db)
    host = repo.get(host_id)
    if not host:
        raise HTTPException(404, "Host not found")
    return repo.update(host, **payload.model_dump(exclude_unset=True))


@router.delete("/{host_id}", status_code=204, dependencies=[Depends(require_operator)])
def delete_host(host_id: int, db: Session = Depends(get_db)):
    repo = HostRepository(db)
    host = repo.get(host_id)
    if not host:
        raise HTTPException(404, "Host not found")
    repo.delete(host)
