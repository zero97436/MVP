from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.license import require_feature
from app.db.session import get_db
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_user)])


@router.get("/sla", dependencies=[Depends(require_feature("sla_reports"))])
def sla(days: int = 30, db: Session = Depends(get_db)):
    return ReportService(db).sla(days=days)


@router.get("/mttr", dependencies=[Depends(require_feature("sla_reports"))])
def mttr(days: int = 30, db: Session = Depends(get_db)):
    return ReportService(db).mttr(days=days)


@router.get("/pdf", dependencies=[Depends(require_feature("pdf_reports"))])
def report_pdf(days: int = 30, db: Session = Depends(get_db)):
    pdf = ReportService(db).pdf(days=days)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="rapport-supervision-{days}j.pdf"'},
    )
