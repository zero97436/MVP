from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_operator
from app.db.session import get_db
from app.services.import_service import ImportService

router = APIRouter(
    prefix="/migrate", tags=["migrate"],
    dependencies=[Depends(get_current_user), Depends(require_operator)],
)


class ImportPayload(BaseModel):
    format: str  # "csv" | "nagios"
    content: str
    dry_run: bool = True


@router.post("")
def migrate(payload: ImportPayload, db: Session = Depends(get_db)):
    svc = ImportService(db)
    if payload.format == "csv":
        hosts, warnings = svc.parse_csv(payload.content)
    elif payload.format == "nagios":
        hosts, warnings = svc.parse_nagios(payload.content)
    else:
        raise HTTPException(400, "format : 'csv' ou 'nagios'")

    if payload.dry_run:
        return {
            "dry_run": True,
            "hosts": [
                {"name": h["name"], "hostname_or_ip": h["hostname_or_ip"],
                 "environment": h.get("environment"), "location": h.get("location"),
                 "template": h.get("template"), "parent": h.get("parent"),
                 "checks": [c["name"] for c in h.get("checks", [])]}
                for h in hosts
            ],
            "warnings": warnings,
        }

    # Limite de licence appliquée avant l'import réel.
    from app.api.routes.hosts import enforce_host_limit
    from app.models.host import Host
    from sqlalchemy import select

    existing_ips = {h.hostname_or_ip for h in db.scalars(select(Host))}
    to_add = sum(1 for h in hosts if h["hostname_or_ip"] not in existing_ips)
    enforce_host_limit(db, adding=to_add)

    result = svc.apply(hosts)
    result["warnings"] = warnings + result["warnings"]
    result["dry_run"] = False
    return result
