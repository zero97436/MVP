from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_operator
from app.db.session import get_db
from app.models.host import Host
from app.services.template_service import TemplateService

router = APIRouter(
    prefix="/check-templates", tags=["check-templates"],
    dependencies=[Depends(get_current_user)],
)


def _out(t) -> dict:
    return {"id": t.id, "name": t.name, "description": t.description, "items": t.items}


class TemplateCreate(BaseModel):
    name: str
    description: str | None = None
    items: list[dict]


class FromHost(BaseModel):
    host_id: int
    name: str
    description: str | None = None


class ApplyPayload(BaseModel):
    host_id: int


@router.get("")
def list_templates(db: Session = Depends(get_db)):
    return [_out(t) for t in TemplateService(db).list()]


@router.post("", status_code=201, dependencies=[Depends(require_operator)])
def create_template(payload: TemplateCreate, db: Session = Depends(get_db)):
    tpl = TemplateService(db).create(payload.name, payload.items, payload.description)
    if not tpl:
        raise HTTPException(400, "Modèle invalide (nom déjà pris ou aucun check valide)")
    return _out(tpl)


@router.post("/from-host", status_code=201, dependencies=[Depends(require_operator)])
def create_from_host(payload: FromHost, db: Session = Depends(get_db)):
    if not db.get(Host, payload.host_id):
        raise HTTPException(404, "Hôte introuvable")
    tpl = TemplateService(db).create_from_host(payload.host_id, payload.name, payload.description)
    if not tpl:
        raise HTTPException(400, "Impossible (hôte sans checks ou nom déjà pris)")
    return _out(tpl)


@router.post("/{template_id}/apply", dependencies=[Depends(require_operator)])
def apply_template(template_id: int, payload: ApplyPayload, db: Session = Depends(get_db)):
    if not db.get(Host, payload.host_id):
        raise HTTPException(404, "Hôte introuvable")
    result = TemplateService(db).apply(template_id, payload.host_id)
    if result is None:
        raise HTTPException(404, "Modèle introuvable")
    return result


@router.delete("/{template_id}", status_code=204, dependencies=[Depends(require_operator)])
def delete_template(template_id: int, db: Session = Depends(get_db)):
    if not TemplateService(db).delete(template_id):
        raise HTTPException(404, "Modèle introuvable")
