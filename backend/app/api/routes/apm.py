from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_ingest_key
from app.db.session import get_db
from app.services.apm_service import ApmService

router = APIRouter(prefix="/apm", tags=["apm"])


class ApmIngest(BaseModel):
    app_name: str = Field(min_length=1, max_length=128)
    requests: int = Field(ge=0)
    errors: int = Field(default=0, ge=0)
    latency_ms: float | None = None
    environment: str = "prod"
    collected_at: datetime | None = None


@router.post("/ingest", status_code=201)
def ingest(payload: ApmIngest, db: Session = Depends(get_db), _: None = Depends(require_ingest_key)):
    sample = ApmService(db).ingest(**payload.model_dump())
    return {"id": sample.id, "app_name": sample.app_name}


@router.get("/apps", dependencies=[Depends(get_current_user)])
def apps(minutes: int = 15, db: Session = Depends(get_db)):
    return ApmService(db).apps(minutes=minutes)


@router.get("/apps/{app_name}/series", dependencies=[Depends(get_current_user)])
def series(app_name: str, hours: int = 24, buckets: int = 48, db: Session = Depends(get_db)):
    return ApmService(db).series(app_name, hours=hours, buckets=min(buckets, 200))
