"""Gestion des tenants (MSP multi-tenant) — admin global + feature multi_tenant."""
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.license import require_feature
from app.db.session import get_db
from app.models.host import Host
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter(
    prefix="/tenants", tags=["tenants"],
    dependencies=[Depends(require_admin), Depends(require_feature("multi_tenant"))],
)


class TenantCreate(BaseModel):
    name: str
    slug: str | None = None


class AssignHost(BaseModel):
    host_id: int
    tenant_id: int | None = None  # null = retirer du tenant (repartage global)


class AssignUser(BaseModel):
    user_id: int
    tenant_id: int | None = None  # null = personnel MSP global


def _slugify(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", v.lower()).strip("-")[:64] or "tenant"


@router.get("")
def list_tenants(db: Session = Depends(get_db)):
    hosts_by = dict(db.execute(
        select(Host.tenant_id, func.count(Host.id)).group_by(Host.tenant_id)
    ).all())
    users_by = dict(db.execute(
        select(User.tenant_id, func.count(User.id)).group_by(User.tenant_id)
    ).all())
    return [
        {"id": t.id, "name": t.name, "slug": t.slug,
         "hosts": hosts_by.get(t.id, 0), "users": users_by.get(t.id, 0)}
        for t in db.scalars(select(Tenant).order_by(Tenant.name))
    ]


@router.post("", status_code=201)
def create_tenant(payload: TenantCreate, db: Session = Depends(get_db)):
    slug = _slugify(payload.slug or payload.name)
    if db.scalar(select(Tenant).where(Tenant.slug == slug)):
        raise HTTPException(400, f"slug déjà utilisé : {slug}")
    t = Tenant(name=payload.name[:128], slug=slug)
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "name": t.name, "slug": t.slug}


@router.delete("/{tenant_id}", status_code=204)
def delete_tenant(tenant_id: int, db: Session = Depends(get_db)):
    t = db.get(Tenant, tenant_id)
    if not t:
        raise HTTPException(404, "Tenant introuvable")
    # Les hôtes/users repassent en global (FK ON DELETE SET NULL).
    db.delete(t)
    db.commit()


@router.post("/assign-host")
def assign_host(payload: AssignHost, db: Session = Depends(get_db)):
    host = db.get(Host, payload.host_id)
    if not host:
        raise HTTPException(404, "Hôte introuvable")
    if payload.tenant_id is not None and not db.get(Tenant, payload.tenant_id):
        raise HTTPException(404, "Tenant introuvable")
    host.tenant_id = payload.tenant_id
    db.commit()
    return {"host_id": host.id, "tenant_id": host.tenant_id}


@router.post("/assign-user")
def assign_user(payload: AssignUser, db: Session = Depends(get_db)):
    u = db.get(User, payload.user_id)
    if not u:
        raise HTTPException(404, "Utilisateur introuvable")
    if payload.tenant_id is not None and not db.get(Tenant, payload.tenant_id):
        raise HTTPException(404, "Tenant introuvable")
    u.tenant_id = payload.tenant_id
    db.commit()
    return {"user_id": u.id, "tenant_id": u.tenant_id}
