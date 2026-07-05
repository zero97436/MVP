from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_operator
from app.core.license import require_feature
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, IncidentOut
from app.services.ai_service import AIService, OllamaError
from app.services.dashboard_service import DashboardService
from app.services.remediation_service import RemediationService


class RemediateRequest(BaseModel):
    action: str

router = APIRouter(
    prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)]
)


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db)):
    return DashboardService(db).summary()


@router.get("/incidents", response_model=list[IncidentOut])
def incidents(db: Session = Depends(get_db)):
    return DashboardService(db).incidents()


# --- Dashboard personnalisable (ordre + visibilité des sections, par utilisateur) ---
DEFAULT_LAYOUT = [
    {"id": "hero", "visible": True},
    {"id": "kpi", "visible": True},
    {"id": "incidents", "visible": True},
    {"id": "trend", "visible": True},
    {"id": "fleet", "visible": True},
]
SECTION_IDS = {s["id"] for s in DEFAULT_LAYOUT}


class LayoutSection(BaseModel):
    id: str
    visible: bool = True


class LayoutIn(BaseModel):
    sections: list[LayoutSection]


@router.get("/layout")
def get_layout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.dashboard_pref import DashboardPref
    from sqlalchemy import select

    pref = db.scalar(select(DashboardPref).where(DashboardPref.user_id == user.id))
    if not pref or not pref.layout:
        return {"sections": DEFAULT_LAYOUT, "custom": False}
    # Complète avec les sections manquantes (nouveaux blocs ajoutés depuis).
    known = {s["id"] for s in pref.layout}
    merged = [s for s in pref.layout if s.get("id") in SECTION_IDS]
    merged += [s for s in DEFAULT_LAYOUT if s["id"] not in known]
    return {"sections": merged, "custom": True}


@router.put("/layout", dependencies=[Depends(require_feature("custom_dashboards"))])
def save_layout(payload: LayoutIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.dashboard_pref import DashboardPref
    from sqlalchemy import select

    sections = [s.model_dump() for s in payload.sections if s.id in SECTION_IDS]
    if not sections:
        raise HTTPException(400, "Aucune section valide")
    pref = db.scalar(select(DashboardPref).where(DashboardPref.user_id == user.id))
    if pref:
        pref.layout = sections
    else:
        db.add(DashboardPref(user_id=user.id, layout=sections))
    db.commit()
    return {"sections": sections, "custom": True}


@router.delete("/layout", status_code=204)
def reset_layout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.dashboard_pref import DashboardPref
    from sqlalchemy import select

    pref = db.scalar(select(DashboardPref).where(DashboardPref.user_id == user.id))
    if pref:
        db.delete(pref)
        db.commit()


@router.post("/incidents/{alert_id}/ack", response_model=IncidentOut)
def acknowledge_incident(
    alert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    alert = DashboardService(db).acknowledge(alert_id, user.email, ack=True)
    if not alert:
        raise HTTPException(404, "Alert not found")
    return _incident_payload(db, alert_id)


@router.post("/incidents/{alert_id}/unack", response_model=IncidentOut)
def unacknowledge_incident(
    alert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    alert = DashboardService(db).acknowledge(alert_id, user.email, ack=False)
    if not alert:
        raise HTTPException(404, "Alert not found")
    return _incident_payload(db, alert_id)


@router.post("/ai-summary")
def ai_summary(db: Session = Depends(get_db)):
    """Résumé santé global généré par l'IA (Ollama)."""
    try:
        return AIService(db).health_summary()
    except OllamaError as exc:
        raise HTTPException(503, str(exc))


@router.post("/incidents/{alert_id}/remediate", dependencies=[Depends(require_feature("remediation"))])
def remediate_incident(
    alert_id: int,
    payload: RemediateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    """Exécute une action de remédiation (liste blanche) validée par l'utilisateur."""
    try:
        result = RemediationService(db).execute(alert_id, payload.action, user.email)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    if result is None:
        raise HTTPException(404, "Alert not found")
    return result


@router.post("/incidents/{alert_id}/analyze")
def analyze_incident(alert_id: int, db: Session = Depends(get_db)):
    """Analyse IA (Ollama) de l'incident : cause probable, impact, remédiation."""
    try:
        result = AIService(db).analyze_incident(alert_id)
    except OllamaError as exc:
        raise HTTPException(503, str(exc))
    if result is None:
        raise HTTPException(404, "Alert not found")
    return result


def _incident_payload(db: Session, alert_id: int) -> dict:
    """Recompose la vue incident (avec host/check) après acquittement."""
    for inc in DashboardService(db).incidents():
        if inc["alert_id"] == alert_id:
            return inc
    raise HTTPException(404, "Alert no longer active")
