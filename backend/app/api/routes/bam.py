from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_operator
from app.db.session import get_db
from app.services.bam_service import BamService

router = APIRouter(prefix="/bam", tags=["bam"], dependencies=[Depends(get_current_user)])


class ServiceCreate(BaseModel):
    name: str
    description: str | None = None
    rule: str = "worst"  # worst | percent
    warning_threshold: float | None = None
    critical_threshold: float | None = None
    category: str = "Général"
    icon: str | None = None


class ServiceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    rule: str | None = None
    category: str | None = None
    icon: str | None = None
    pos_x: int | None = None
    pos_y: int | None = None


class TilePosition(BaseModel):
    id: int
    pos_x: int | None = None
    pos_y: int | None = None


class LayoutPayload(BaseModel):
    positions: list[TilePosition]


class ComponentCreate(BaseModel):
    check_id: int | None = None
    host_id: int | None = None
    label: str | None = None


@router.get("")
def list_services(db: Session = Depends(get_db)):
    return BamService(db).list()


@router.post("", status_code=201, dependencies=[Depends(require_operator)])
def create_service(payload: ServiceCreate, db: Session = Depends(get_db)):
    if payload.rule not in ("worst", "percent"):
        raise HTTPException(400, "rule doit être 'worst' ou 'percent'")
    bs = BamService(db).create(**payload.model_dump())
    return {"id": bs.id, "name": bs.name}


@router.patch("/{bs_id}", dependencies=[Depends(require_operator)])
def update_service(bs_id: int, payload: ServiceUpdate, db: Session = Depends(get_db)):
    if payload.rule is not None and payload.rule not in ("worst", "percent"):
        raise HTTPException(400, "rule doit être 'worst' ou 'percent'")
    bs = BamService(db).update(bs_id, **payload.model_dump(exclude_unset=True))
    if not bs:
        raise HTTPException(404, "Service métier introuvable")
    return {"id": bs.id}


@router.post("/layout", dependencies=[Depends(require_operator)])
def save_layout(payload: LayoutPayload, db: Session = Depends(get_db)):
    count = BamService(db).set_positions([p.model_dump() for p in payload.positions])
    return {"updated": count}


@router.delete("/{bs_id}", status_code=204, dependencies=[Depends(require_operator)])
def delete_service(bs_id: int, db: Session = Depends(get_db)):
    if not BamService(db).delete(bs_id):
        raise HTTPException(404, "Service métier introuvable")


@router.post("/{bs_id}/components", status_code=201, dependencies=[Depends(require_operator)])
def add_component(bs_id: int, payload: ComponentCreate, db: Session = Depends(get_db)):
    if not payload.check_id and not payload.host_id:
        raise HTTPException(400, "Fournir check_id ou host_id")
    comp = BamService(db).add_component(bs_id, **payload.model_dump())
    if not comp:
        raise HTTPException(404, "Service métier introuvable")
    return {"id": comp.id}


@router.delete("/components/{comp_id}", status_code=204, dependencies=[Depends(require_operator)])
def remove_component(comp_id: int, db: Session = Depends(get_db)):
    if not BamService(db).remove_component(comp_id):
        raise HTTPException(404, "Composant introuvable")
