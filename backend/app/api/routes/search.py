"""Recherche globale : hôtes, checks, tickets, événements (Ctrl+K)."""
from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.check import Check
from app.models.event_log import EventLog
from app.models.host import Host
from app.models.ticket import Ticket

router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(get_current_user)])

LIMIT = 5


@router.get("")
def search(q: str = "", db: Session = Depends(get_db)):
    q = q.strip()
    if len(q) < 2:
        return {"hosts": [], "checks": [], "tickets": [], "events": []}
    like = f"%{q}%"

    hosts = db.scalars(
        select(Host).where(or_(Host.name.ilike(like), Host.hostname_or_ip.ilike(like)))
        .order_by(Host.name).limit(LIMIT)
    ).all()
    checks = db.scalars(
        select(Check).where(Check.name.ilike(like)).order_by(Check.name).limit(LIMIT)
    ).all()
    host_names = {h.id: h.name for h in db.scalars(
        select(Host).where(Host.id.in_({c.host_id for c in checks}))
    )} if checks else {}
    tickets = db.scalars(
        select(Ticket).where(Ticket.title.ilike(like))
        .order_by(Ticket.created_at.desc()).limit(LIMIT)
    ).all()
    events = db.scalars(
        select(EventLog).where(EventLog.message.ilike(like))
        .order_by(EventLog.created_at.desc()).limit(LIMIT)
    ).all()

    return {
        "hosts": [
            {"id": h.id, "name": h.name, "hostname_or_ip": h.hostname_or_ip}
            for h in hosts
        ],
        "checks": [
            {"id": c.id, "name": c.name, "type": c.type,
             "host_name": host_names.get(c.host_id, ""), "last_status": c.last_status}
            for c in checks
        ],
        "tickets": [
            {"id": t.id, "title": t.title, "status": t.status, "priority": t.priority}
            for t in tickets
        ],
        "events": [
            {"id": e.id, "message": e.message, "level": e.level,
             "created_at": e.created_at.isoformat() if e.created_at else None}
            for e in events
        ],
    }
