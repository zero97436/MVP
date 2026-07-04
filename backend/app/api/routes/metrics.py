from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_ingest_key
from app.db.session import get_db
from app.repositories.metric_repo import MetricRepository
from app.schemas.metric import MetricHourlyOut, MetricIngest, MetricLatest, MetricOut
from app.services.downsample_service import DownsampleService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.post("/ingest", response_model=MetricOut, status_code=201)
def ingest(
    payload: MetricIngest,
    db: Session = Depends(get_db),
    _: None = Depends(require_ingest_key),
):
    repo = MetricRepository(db)
    host_id = repo.resolve_host_id(payload.host_id, payload.hostname_or_ip)
    if host_id is None:
        raise HTTPException(404, "Host not found (host_id / hostname_or_ip)")
    return repo.add(
        host_id=host_id,
        cpu_percent=payload.cpu_percent,
        mem_percent=payload.mem_percent,
        disk_percent=payload.disk_percent,
        disks=payload.disks,
        net_mbps=payload.net_mbps,
        process_count=payload.process_count,
        load1=payload.load1,
        temperature=payload.temperature,
        collected_at=payload.collected_at,
    )


@router.get(
    "/hosts/{host_id}",
    response_model=list[MetricOut],
    dependencies=[Depends(get_current_user)],
)
def host_metrics(
    host_id: int,
    hours: int = 24,
    limit: int = 1000,
    db: Session = Depends(get_db),
):
    return MetricRepository(db).for_host(host_id, hours=hours, limit=limit)


@router.get("/snmp/interfaces", dependencies=[Depends(get_current_user)])
def snmp_interfaces(host: str, community: str = "public", version: str = "2c", timeout: int = 3):
    """Découverte des interfaces SNMP d'un équipement (index + nom) pour les checks de trafic."""
    from app.checks.plugins._snmp import list_interfaces

    try:
        return {"interfaces": list_interfaces(host, community, version, timeout)}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"SNMP indisponible : {str(exc)[:120]}")


@router.get(
    "/hosts/{host_id}/hourly",
    response_model=list[MetricHourlyOut],
    dependencies=[Depends(get_current_user)],
)
def host_metrics_hourly(host_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Rollups horaires (downsampling) pour des tendances long terme."""
    return DownsampleService(db).for_host(host_id, days=days)


@router.get(
    "/hosts/{host_id}/latest",
    response_model=MetricLatest,
    dependencies=[Depends(get_current_user)],
)
def host_latest(host_id: int, db: Session = Depends(get_db)):
    m = MetricRepository(db).latest(host_id)
    if not m:
        return MetricLatest(host_id=host_id)
    return m
