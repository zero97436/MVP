from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_operator
from app.db.session import get_db
from app.models.alert import Alert
from app.models.ticket import Ticket
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"], dependencies=[Depends(get_current_user)])


def _out(t: Ticket) -> dict:
    return {
        "id": t.id, "alert_id": t.alert_id, "title": t.title, "description": t.description,
        "status": t.status, "priority": t.priority, "provider": t.provider,
        "external_id": t.external_id, "external_url": t.external_url,
        "created_by": t.created_by,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "assigned_to_id": t.assigned_to_id,
        "assigned_to": t.assignee.email if t.assignee else None,
        "tasks": [
            {"id": task.id, "label": task.label, "done": task.done}
            for task in sorted(t.tasks, key=lambda x: x.position)
        ],
        "comments": [
            {"id": c.id, "author": c.author, "body": c.body,
             "created_at": c.created_at.isoformat() if c.created_at else None}
            for c in t.comments
        ],
    }


class TicketCreate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str = "medium"
    alert_id: int | None = None


class TicketStatus(BaseModel):
    status: str


class TicketPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    assigned_to_id: int | None = None  # null explicite = désassigner


@router.get("/config")
def config(db: Session = Depends(get_db)):
    return TicketService(db).config()


@router.get("")
def list_tickets(status: str | None = None, db: Session = Depends(get_db),
                user=Depends(get_current_user)):
    from app.core.tenancy import is_scoped, visible_host_ids
    from app.models.check import Check

    tickets = TicketService(db).list(status=status)
    if is_scoped(user):
        allowed = visible_host_ids(db, user)
        # Un ticket est visible s'il n'est lié à aucune alerte, ou si l'hôte de
        # son alerte appartient au tenant.
        def visible(t):
            if not t.alert_id:
                return False  # tickets non rattachés = cachés aux tenants (créés par le MSP)
            alert = db.get(Alert, t.alert_id)
            check = db.get(Check, alert.check_id) if alert else None
            return bool(check and check.host_id in allowed)
        tickets = [t for t in tickets if visible(t)]
    return [_out(t) for t in tickets]


@router.post("", status_code=201, dependencies=[Depends(require_operator)])
def create_ticket(payload: TicketCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    svc = TicketService(db)
    if payload.alert_id and not payload.title:
        alert = db.get(Alert, payload.alert_id)
        if not alert:
            raise HTTPException(404, "Incident introuvable")
        ticket = svc.create_from_alert(alert, created_by=user.email)
    else:
        if not payload.title:
            raise HTTPException(400, "title requis")
        ticket = svc.create(
            title=payload.title, description=payload.description,
            priority=payload.priority, alert_id=payload.alert_id, created_by=user.email,
        )
    return _out(ticket)


@router.patch("/{ticket_id}")
def patch_ticket(
    ticket_id: int,
    payload: TicketPatch,
    user=Depends(require_operator),
    db: Session = Depends(get_db),
):
    """Édition complète (titre, description, priorité, statut, assignation) — journalisée en suivi."""
    kwargs = payload.model_dump(exclude_unset=True)  # distingue "absent" de "null"
    ticket = TicketService(db).update(ticket_id, author=user.email, **kwargs)
    if not ticket:
        raise HTTPException(404, "Ticket introuvable")
    return _out(ticket)


@router.get("/assignees")
def assignees(db: Session = Depends(get_db)):
    """Utilisateurs actifs assignables (accessible aux opérateurs, sans détails admin)."""
    from sqlalchemy import select

    from app.models.user import User as UserModel

    users = db.scalars(select(UserModel).where(UserModel.is_active.is_(True)).order_by(UserModel.email))
    return [{"id": u.id, "email": u.email, "full_name": u.full_name} for u in users]


@router.delete("/{ticket_id}", status_code=204, dependencies=[Depends(require_operator)])
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    if not TicketService(db).delete(ticket_id):
        raise HTTPException(404, "Ticket introuvable")


# ---- Tâches (checklist) ----
class TaskCreate(BaseModel):
    label: str


class TaskUpdate(BaseModel):
    done: bool | None = None
    label: str | None = None


@router.post("/{ticket_id}/tasks", status_code=201, dependencies=[Depends(require_operator)])
def add_task(ticket_id: int, payload: TaskCreate, db: Session = Depends(get_db)):
    if not payload.label.strip():
        raise HTTPException(400, "label requis")
    task = TicketService(db).add_task(ticket_id, payload.label.strip())
    if not task:
        raise HTTPException(404, "Ticket introuvable")
    return {"id": task.id, "label": task.label, "done": task.done}


@router.patch("/tasks/{task_id}", dependencies=[Depends(require_operator)])
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = TicketService(db).update_task(task_id, done=payload.done, label=payload.label)
    if not task:
        raise HTTPException(404, "Tâche introuvable")
    return {"id": task.id, "label": task.label, "done": task.done}


@router.delete("/tasks/{task_id}", status_code=204, dependencies=[Depends(require_operator)])
def delete_task(task_id: int, db: Session = Depends(get_db)):
    if not TicketService(db).delete_task(task_id):
        raise HTTPException(404, "Tâche introuvable")


# ---- Suivis (commentaires) ----
class CommentCreate(BaseModel):
    body: str


@router.post("/{ticket_id}/comments", status_code=201, dependencies=[Depends(require_operator)])
def add_comment(
    ticket_id: int, payload: CommentCreate,
    user=Depends(get_current_user), db: Session = Depends(get_db),
):
    if not payload.body.strip():
        raise HTTPException(400, "body requis")
    c = TicketService(db).add_comment(ticket_id, payload.body.strip(), author=user.email)
    if not c:
        raise HTTPException(404, "Ticket introuvable")
    return {"id": c.id, "author": c.author, "body": c.body,
            "created_at": c.created_at.isoformat() if c.created_at else None}


@router.delete("/comments/{comment_id}", status_code=204, dependencies=[Depends(require_operator)])
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    if not TicketService(db).delete_comment(comment_id):
        raise HTTPException(404, "Suivi introuvable")
