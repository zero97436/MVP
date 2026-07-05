"""Journal d'audit (Enterprise) : consultation filtrable, enregistrements immuables."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.license import require_feature
from app.db.session import get_db
from app.models.audit_log import AuditLog

router = APIRouter(
    prefix="/audit", tags=["audit"],
    dependencies=[Depends(require_admin), Depends(require_feature("audit"))],
)


@router.get("")
def list_audit(
    user: str | None = None,
    action: str | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    if user:
        stmt = stmt.where(AuditLog.user_email.ilike(f"%{user}%"))
    if action:
        stmt = stmt.where(AuditLog.action.ilike(f"%{action}%"))
    if q:
        stmt = stmt.where(AuditLog.path.ilike(f"%{q}%"))
    rows = db.scalars(stmt.offset(offset).limit(min(limit, 500))).all()
    return [
        {
            "id": r.id, "user_email": r.user_email, "method": r.method,
            "path": r.path, "action": r.action, "status_code": r.status_code,
            "ip": r.ip, "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
