"""Cloisonnement multi-tenant (MSP) — Business/Enterprise.

Règle : un utilisateur rattaché à un tenant (user.tenant_id non NULL) ne voit
que les hôtes de son tenant, et par transitivité tout ce qui en dépend (checks,
alertes, incidents, événements, tickets, métriques). Le personnel MSP « global »
(tenant_id NULL) voit tout.

⚠️ Entièrement neutralisé sans la feature « multi_tenant » : `is_scoped` renvoie
toujours False, donc AUCUN filtrage — comportement mono-tenant historique.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.license import has_feature
from app.models.host import Host
from app.models.user import User


def is_scoped(user: User) -> bool:
    """Vrai si l'utilisateur doit être cloisonné à son tenant."""
    return has_feature("multi_tenant") and getattr(user, "tenant_id", None) is not None


def visible_host_ids(db: Session, user: User) -> set[int] | None:
    """None = accès total (staff global ou feature off). Sinon les host ids du tenant."""
    if not is_scoped(user):
        return None
    return set(db.scalars(select(Host.id).where(Host.tenant_id == user.tenant_id)))


def host_visible(user: User, host: Host | None) -> bool:
    """Vrai si l'utilisateur a le droit de voir/agir sur cet hôte."""
    if not is_scoped(user):
        return True
    return host is not None and host.tenant_id == user.tenant_id


def scope_hosts(stmt, user: User):
    """Ajoute le filtre tenant à une requête SELECT sur Host (si cloisonné)."""
    if is_scoped(user):
        return stmt.where(Host.tenant_id == user.tenant_id)
    return stmt
