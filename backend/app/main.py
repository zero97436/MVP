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
    auth,
    bam,
    branding,
    checks,
    check_templates,
    dashboard,
    discovery,
    docker,
    events,
    hosts,
    maintenance,
    metrics,
    migrate,
    public_status,
    reports,
    search,
    sso,
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
for module in (auth, hosts, checks, dashboard, metrics, users, admin, ai, agent, maintenance, events, discovery, reports, bam, tickets, apm, docker, check_templates, public_status, search, migrate, branding, sso, settings_routes):
    app.include_router(module.router, prefix=settings.API_PREFIX)


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
