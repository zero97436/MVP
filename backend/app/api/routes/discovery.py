from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_operator
from app.checks.registry import get_check
from app.db.session import get_db
from app.repositories.check_repo import CheckRepository
from app.repositories.host_repo import HostRepository
from app.services.discovery_service import DiscoveryService
from app.services.event_service import EventService

router = APIRouter(
    prefix="/discovery", tags=["discovery"], dependencies=[Depends(get_current_user)]
)


class ScanRequest(BaseModel):
    target: str  # CIDR (ex. 192.168.1.0/24), plage ou IP
    ports: list[int] | None = None


class ImportItem(BaseModel):
    name: str
    hostname_or_ip: str
    environment: str = "decouvert"
    checks: list[dict[str, Any]] = Field(default_factory=list)


class ImportRequest(BaseModel):
    items: list[ImportItem]


@router.post("/scan", dependencies=[Depends(require_operator)])
def scan(payload: ScanRequest, db: Session = Depends(get_db)):
    try:
        return {"results": DiscoveryService(db).scan(payload.target, payload.ports)}
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.post("/import", dependencies=[Depends(require_operator)])
def import_hosts(payload: ImportRequest, db: Session = Depends(get_db)):
    from app.api.routes.hosts import enforce_host_limit

    host_repo = HostRepository(db)
    check_repo = CheckRepository(db)
    existing = {h.hostname_or_ip: h for h in host_repo.list()}
    to_add = sum(1 for i in payload.items if i.hostname_or_ip not in existing)
    enforce_host_limit(db, adding=to_add)
    created = []
    for item in payload.items:
        if item.hostname_or_ip in existing:
            continue  # déjà supervisé -> on saute
        host = host_repo.create(
            name=item.name or item.hostname_or_ip,
            hostname_or_ip=item.hostname_or_ip,
            environment=item.environment,
            description="Importé par découverte réseau",
        )
        for c in item.checks:
            if get_check(c.get("type")) is None:
                continue
            check_repo.create(
                host_id=host.id, name=(c.get("name") or c["type"])[:255], type=c["type"],
                interval_seconds=int(c.get("interval_seconds", 60)),
                timeout_seconds=int(c.get("timeout_seconds", 10)),
                config_json=c.get("config_json") or {},
            )
        created.append({"host_id": host.id, "name": host.name})

    if created:
        EventService(db).record(
            "discovery_import", f"{len(created)} hôte(s) importé(s) par découverte",
            meta={"count": len(created)},
        )
    return {"imported": len(created), "hosts": created}
