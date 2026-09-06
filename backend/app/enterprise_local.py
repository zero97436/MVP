"""Bundle Enterprise INTERNE — PHASE 1a (transitoire).

Regroupe l'enregistrement des modules payants derrière le même contrat
`install(app, api_prefix)` que le futur paquet privé `orbisys_enterprise`.

En Phase 1b, ce fichier et les routers qu'il importe (sso, ha, tenants, audit,
reports) seront DÉPLACÉS vers le dépôt privé `orbisys-enterprise`, puis retirés
du dépôt public. Le noyau ne changera pas : `app.plugins.load_enterprise` importe
d'abord le paquet externe et ne retombe sur ce bundle que s'il est absent.

Chaque router conserve sa garde `require_feature(...)` (défense en profondeur).
"""
from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import audit, ha, reports, sso, tenants
from app.audit_middleware import add_audit_middleware

# Modules payants exposant un router dédié (Tier A).
_ENTERPRISE_ROUTERS = (reports, sso, audit, tenants, ha)


def install(app: FastAPI, api_prefix: str) -> None:
    """Enregistre les routers payants + le middleware d'audit."""
    for module in _ENTERPRISE_ROUTERS:
        app.include_router(module.router, prefix=api_prefix)
    add_audit_middleware(app)
