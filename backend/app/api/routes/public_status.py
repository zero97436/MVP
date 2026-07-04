"""Page de statut publique : état des services métier SANS authentification.

N'expose volontairement AUCUN détail technique : ni hôtes, ni checks, ni
composants — uniquement le nom, la catégorie et l'état des services métier.
Désactivable via STATUS_PAGE_ENABLED=false.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.services.bam_service import BamService

router = APIRouter(prefix="/public", tags=["public"])

SEVERITY = {"CRITICAL": 0, "WARNING": 1, "UNKNOWN": 2, "OK": 3}


@router.get("/status")
def public_status(db: Session = Depends(get_db)):
    if not settings.STATUS_PAGE_ENABLED:
        raise HTTPException(404, "Page de statut désactivée")

    services = BamService(db).list()
    public = [
        {
            "name": s["name"],
            "description": s["description"],
            "category": s["category"],
            "status": s["status"],
        }
        for s in services
    ]
    statuses = [s["status"] for s in public]
    overall = (
        "CRITICAL" if "CRITICAL" in statuses
        else "WARNING" if "WARNING" in statuses
        else "UNKNOWN" if not statuses
        else "OK"
    )
    return {
        "title": settings.STATUS_PAGE_TITLE,
        "overall": overall,
        "services": sorted(public, key=lambda s: (SEVERITY.get(s["status"], 2), s["name"])),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
