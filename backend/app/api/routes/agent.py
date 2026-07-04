from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_ingest_key
from app.db.session import get_db
from app.models.agent_command import AgentCommand
from app.models.check import Check
from app.models.host import Host
from app.repositories.check_repo import CheckRepository
from app.repositories.metric_repo import MetricRepository
from app.services.check_service import CheckService

router = APIRouter(prefix="/agent", tags=["agent"])


class AssignedCheck(BaseModel):
    id: int
    type: str
    target: str
    timeout_seconds: int
    warning_threshold: float | None = None
    critical_threshold: float | None = None
    config: dict | None = None


class CheckResultIn(BaseModel):
    status: str
    value: float | None = None
    message: str | None = None
    perfdata: dict | None = None
    duration_ms: int | None = None


class CommandOut(BaseModel):
    id: int
    action: str
    params: dict | None = None


class CommandResult(BaseModel):
    status: str  # done | failed
    result: str | None = None


@router.get("/commands", response_model=list[CommandOut], dependencies=[Depends(require_ingest_key)])
def poll_commands(
    host_id: int | None = None,
    hostname_or_ip: str | None = None,
    db: Session = Depends(get_db),
):
    """L'agent récupère ses commandes en attente (et les passe en 'sent')."""
    resolved = MetricRepository(db).resolve_host_id(host_id, hostname_or_ip)
    if resolved is None:
        raise HTTPException(404, "Host not found")
    pending = list(
        db.scalars(
            select(AgentCommand)
            .where(AgentCommand.host_id == resolved, AgentCommand.status == "pending")
            .order_by(AgentCommand.created_at.asc())
        )
    )
    for cmd in pending:
        cmd.status = "sent"
    db.commit()
    return pending


@router.post("/commands/{command_id}/result", dependencies=[Depends(require_ingest_key)])
def report_result(command_id: int, payload: CommandResult, db: Session = Depends(get_db)):
    cmd = db.get(AgentCommand, command_id)
    if not cmd:
        raise HTTPException(404, "Command not found")
    cmd.status = "done" if payload.status == "done" else "failed"
    cmd.result = payload.result
    cmd.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}


@router.get("/checks", response_model=list[AssignedCheck], dependencies=[Depends(require_ingest_key)])
def assigned_checks(
    host_id: int | None = None,
    hostname_or_ip: str | None = None,
    db: Session = Depends(get_db),
):
    """Checks que CET agent doit exécuter (executor_host_id == cet hôte)."""
    prober = MetricRepository(db).resolve_host_id(host_id, hostname_or_ip)
    if prober is None:
        raise HTTPException(404, "Host not found")
    checks = db.scalars(
        select(Check).where(
            Check.executor_host_id == prober, Check.is_active.is_(True)
        )
    ).all()
    out = []
    for c in checks:
        target = db.get(Host, c.host_id)
        out.append(
            AssignedCheck(
                id=c.id,
                type=c.type,
                target=target.hostname_or_ip if target else "",
                timeout_seconds=c.timeout_seconds,
                warning_threshold=c.warning_threshold,
                critical_threshold=c.critical_threshold,
                config=c.config_json or {},
            )
        )
    return out


@router.post("/checks/{check_id}/result", dependencies=[Depends(require_ingest_key)])
def ingest_check_result(check_id: int, payload: CheckResultIn, db: Session = Depends(get_db)):
    check = CheckRepository(db).get(check_id)
    if not check:
        raise HTTPException(404, "Check not found")
    CheckService(db).ingest_external_result(
        check,
        status=payload.status,
        value=payload.value,
        message=payload.message,
        perfdata=payload.perfdata,
        duration_ms=payload.duration_ms,
    )
    return {"ok": True}


@router.get("/commands/{command_id}", dependencies=[Depends(get_current_user)])
def get_command(command_id: int, db: Session = Depends(get_db)):
    """Suivi d'une commande (pour l'UI : statut + résultat)."""
    cmd = db.get(AgentCommand, command_id)
    if not cmd:
        raise HTTPException(404, "Command not found")
    return {
        "id": cmd.id,
        "action": cmd.action,
        "status": cmd.status,
        "result": cmd.result,
        "created_at": cmd.created_at,
        "completed_at": cmd.completed_at,
    }
