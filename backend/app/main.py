"""Point d'entrée FastAPI."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import time

from app.api.routes import (
    admin,
    agent,
    ai,
    apm,
    audit,
    auth,
    bam,
    branding,
    checks,
    check_templates,
    dashboard,
    discovery,
    docker,
    events,
    ha,
    hosts,
    knowledge,
    maintenance,
    metrics,
    migrate,
    public_status,
    reports,
    search,
    sso,
    tenants,
    tickets,
    users,
    settings as settings_routes,
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("%s started (debug=%s)", settings.APP_NAME, settings.DEBUG)
    yield


app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # configurable via CORS_ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des routers sous /api.
for module in (auth, hosts, checks, dashboard, metrics, users, admin, ai, agent, maintenance, events, discovery, reports, bam, tickets, apm, docker, check_templates, public_status, search, migrate, branding, sso, audit, tenants, ha, knowledge, settings_routes):
    app.include_router(module.router, prefix=settings.API_PREFIX)


# --- Journal d'audit (Enterprise) : trace les écritures API + connexions ---
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


@app.middleware("http")
async def audit_middleware(request, call_next):
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


# --- Auto-instrumentation APM (Opsora se supervise lui-même) ---
# Accumule requêtes/erreurs/latence en mémoire et flush en base toutes les ~30 s.
_apm_buf = {"requests": 0, "errors": 0, "latency_sum": 0.0, "since": time.monotonic()}


@app.middleware("http")
async def apm_middleware(request, call_next):
    start = time.perf_counter()
    status_code = 500  # si call_next lève, on compte une erreur
    try:
        response = await call_next(request)
        status_code = response.status_code
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        _apm_buf["requests"] += 1
        _apm_buf["latency_sum"] += elapsed_ms
        if status_code >= 500:
            _apm_buf["errors"] += 1
        if time.monotonic() - _apm_buf["since"] >= 30 and _apm_buf["requests"]:
            _flush_apm()
    return response


def _flush_apm() -> None:
    from app.db.session import SessionLocal
    from app.services.apm_service import ApmService

    reqs, errs = _apm_buf["requests"], _apm_buf["errors"]
    lat = _apm_buf["latency_sum"] / reqs if reqs else None
    _apm_buf.update({"requests": 0, "errors": 0, "latency_sum": 0.0, "since": time.monotonic()})
    try:
        with SessionLocal() as db:
            ApmService(db).ingest(
                app_name="opsora", requests=reqs, errors=errs, latency_ms=lat,
            )
    except Exception as exc:  # noqa: BLE001 — l'APM ne doit jamais casser l'API
        logger.debug("Flush APM interne ignoré : %s", exc)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "app": settings.APP_NAME}
