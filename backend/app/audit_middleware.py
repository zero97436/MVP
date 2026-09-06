"""Middleware d'audit (Enterprise) : trace les écritures API + connexions.

Extrait de main.py en Phase 1a de la séparation open-core. Attaché uniquement
lorsque l'édition Enterprise est chargée (voir app.plugins / app.enterprise_local).
La garde `has_feature("audit")` reste en défense en profondeur.
"""
from __future__ import annotations

from fastapi import FastAPI

from app.core.logging import get_logger

logger = get_logger(__name__)

# Méthodes considérées comme des écritures traçables.
AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# Endpoints machine-à-machine bruyants ou sans intérêt d'audit humain.
AUDIT_EXCLUDED_PREFIXES = ("/api/metrics/ingest", "/api/apm/ingest", "/api/agent/", "/api/dashboard/ai-summary")


def _audit_action(method: str, path: str) -> str:
    """Ex. POST /api/hosts -> 'hosts:create' ; DELETE /api/checks/3 -> 'checks:delete'."""
    parts = [p for p in path.split("/") if p and p != "api"]
    resource = parts[0] if parts else "?"
    verb = {"POST": "create", "PUT": "update", "PATCH": "update", "DELETE": "delete"}[method]
    if resource == "auth":
        return "auth:login"
    if len(parts) >= 2 and not parts[-1].isdigit():
        return f"{resource}:{parts[-1][:24]}"
    return f"{resource}:{verb}"


def add_audit_middleware(app: FastAPI) -> None:
    """Attache le middleware d'audit à l'application."""

    @app.middleware("http")
    async def audit_middleware(request, call_next):  # noqa: ANN001, ANN201
        response = await call_next(request)
        try:
            from app.core.license import has_feature

            path = request.url.path
            if (
                request.method in AUDIT_METHODS
                and path.startswith("/api/")
                and not any(path.startswith(p) for p in AUDIT_EXCLUDED_PREFIXES)
                and has_feature("audit")
            ):
                from app.core.security import decode_access_token
                from app.db.session import SessionLocal
                from app.models.audit_log import AuditLog

                email = None
                auth_header = request.headers.get("authorization", "")
                if auth_header.lower().startswith("bearer "):
                    payload = decode_access_token(auth_header[7:])
                    email = payload.get("sub") if payload else None
                fwd = request.headers.get("x-forwarded-for")
                ip = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else None)
                with SessionLocal() as db:
                    db.add(AuditLog(
                        user_email=email, method=request.method, path=path[:255],
                        action=_audit_action(request.method, path),
                        status_code=response.status_code, ip=ip,
                    ))
                    db.commit()
        except Exception as exc:  # noqa: BLE001 — l'audit ne doit jamais casser l'API
            logger.debug("Audit ignoré : %s", exc)
        return response
