"""Gestion des rôles personnalisés (admin) : droits de modification par section."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.rbac import BUILTIN_ROLES, SECTION_LABELS, SECTIONS
from app.db.session import get_db
from app.models.role import Role
from app.models.user import User

router = APIRouter(prefix="/roles", tags=["roles"], dependencies=[Depends(require_admin)])


class RoleIn(BaseModel):
    name: str
    description: str | None = None
    permissions: list[str] = []


@router.get("")
def list_roles(db: Session = Depends(get_db)):
    """Rôles intégrés (virtuels) + personnalisés + catalogue des sections."""
    builtin = [
        {"name": "admin", "builtin": True, "description": "Accès total", "permissions": list(SECTIONS)},
        {"name": "operator", "builtin": True, "description": "Modification sur toutes les sections", "permissions": list(SECTIONS)},
        {"name": "viewer", "builtin": True, "description": "Lecture seule", "permissions": []},
    ]
    custom = [
        {"id": r.id, "name": r.name, "builtin": False, "description": r.description,
         "permissions": [s for s in (r.permissions or []) if s in SECTIONS]}
        for r in db.scalars(select(Role).order_by(Role.name))
    ]
    return {
        "sections": [{"key": s, "label": SECTION_LABELS.get(s, s)} for s in SECTIONS],
        "roles": builtin + custom,
    }


@router.post("", status_code=201)
def create_role(payload: RoleIn, db: Session = Depends(get_db)):
    name = payload.name.strip().lower()
    if not name:
        raise HTTPException(400, "Nom requis")
    if name in BUILTIN_ROLES:
        raise HTTPException(400, "Ce nom est réservé (rôle intégré)")
    if db.scalar(select(Role).where(Role.name == name)):
        raise HTTPException(400, "Un rôle porte déjà ce nom")
    role = Role(name=name[:64], description=(payload.description or None),
                permissions=[s for s in payload.permissions if s in SECTIONS])
    db.add(role)
    db.commit()
    db.refresh(role)
    return {"id": role.id, "name": role.name}


@router.put("/{role_id}")
def update_role(role_id: int, payload: RoleIn, db: Session = Depends(get_db)):
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(404, "Rôle introuvable")
    role.description = payload.description or None
    role.permissions = [s for s in payload.permissions if s in SECTIONS]
    db.commit()
    return {"id": role.id, "name": role.name, "permissions": role.permissions}


@router.delete("/{role_id}", status_code=204)
def delete_role(role_id: int, db: Session = Depends(get_db)):
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(404, "Rôle introuvable")
    # Les utilisateurs de ce rôle repassent en lecture seule.
    for u in db.scalars(select(User).where(User.role == role.name)):
        u.role = "viewer"
    db.delete(role)
    db.commit()
