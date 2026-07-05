"""Personnalisation de marque (plan Professional).

GET  /branding : PUBLIC (la page de login/statut en a besoin avant authentification).
                 N'expose que du contenu d'affichage, jamais de donnée sensible.
PUT  /branding : admin + feature « branding » (Professional).
"""
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.license import has_feature, require_feature
from app.db.session import get_db
from app.models.branding import Branding

router = APIRouter(prefix="/branding", tags=["branding"])

DEFAULTS = {
    "display_name": "Opsora",
    "tagline": "Surveillez. Comprenez. Agissez.",
    "logo_url": None,
    "accent_color": None,
    "custom": False,
}

_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class BrandingIn(BaseModel):
    display_name: str | None = None
    tagline: str | None = None
    logo_url: str | None = None
    accent_color: str | None = None


def _get_row(db: Session) -> Branding | None:
    return db.get(Branding, 1)


@router.get("")
def get_branding(db: Session = Depends(get_db)):
    # Sans licence Pro, on sert toujours l'identité par défaut (même si une
    # personnalisation a été enregistrée avant l'expiration de la licence).
    row = _get_row(db)
    if not row or not has_feature("branding"):
        return dict(DEFAULTS)
    return {
        "display_name": row.display_name or DEFAULTS["display_name"],
        "tagline": row.tagline or DEFAULTS["tagline"],
        "logo_url": row.logo_url or None,
        "accent_color": row.accent_color or None,
        "custom": True,
    }


@router.put("", dependencies=[Depends(require_admin), Depends(require_feature("branding"))])
def set_branding(payload: BrandingIn, db: Session = Depends(get_db)):
    if payload.accent_color and not _COLOR_RE.match(payload.accent_color):
        raise HTTPException(400, "accent_color : format attendu #RRGGBB")
    if payload.logo_url and not (
        payload.logo_url.startswith("https://")
        or payload.logo_url.startswith("http://")
        or payload.logo_url.startswith("data:image/")
    ):
        raise HTTPException(400, "logo_url : URL http(s) ou data:image/… attendue")

    row = _get_row(db)
    if not row:
        row = Branding(id=1)
        db.add(row)
    row.display_name = (payload.display_name or "").strip()[:64] or None
    row.tagline = (payload.tagline or "").strip()[:128] or None
    row.logo_url = payload.logo_url or None
    row.accent_color = payload.accent_color or None
    db.commit()
    return get_branding(db)


@router.delete("", status_code=204, dependencies=[Depends(require_admin)])
def reset_branding(db: Session = Depends(get_db)):
    row = _get_row(db)
    if row:
        db.delete(row)
        db.commit()
