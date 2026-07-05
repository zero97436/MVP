"""ITSM / ticketing : création de tickets (interne) + push vers un outil externe.

Providers supportés :
  - internal    : ticket stocké localement uniquement
  - webhook     : POST JSON générique vers ITSM_URL
  - jira        : POST /rest/api/2/issue (basic auth e-mail:token)
  - servicenow  : POST /api/now/table/incident (basic auth user:token)

La configuration vient des variables d'environnement (voir Settings.ITSM_*).
Les échecs de push n'empêchent JAMAIS la création locale du ticket.
"""
from __future__ import annotations

import base64

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.alert import Alert
from app.models.check import Check
from app.models.ticket import Ticket, TicketComment, TicketTask

STATUSES = ("open", "in_progress", "resolved", "closed")
_UNSET = object()  # sentinelle : distinguer "non fourni" de "null" (désassigner)

logger = get_logger(__name__)

PRIORITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


class TicketService:
    def __init__(self, db: Session):
        self.db = db

    # ---- lecture ----
    def list(self, status: str | None = None) -> list[Ticket]:
        stmt = select(Ticket).order_by(Ticket.created_at.desc())
        if status:
            stmt = stmt.where(Ticket.status == status)
        return list(self.db.scalars(stmt))

    def get(self, ticket_id: int) -> Ticket | None:
        return self.db.get(Ticket, ticket_id)

    def config(self) -> dict:
        """État de l'intégration (sans secrets)."""
        from app.core.license import has_feature

        return {
            "provider": settings.ITSM_PROVIDER,
            "configured": bool(settings.ITSM_PROVIDER == "internal" or settings.ITSM_URL),
            "auto_create": settings.ITSM_AUTO_CREATE,
            "target": settings.ITSM_URL or "local",
            "connectors_licensed": has_feature("itsm_connectors"),
        }

    # ---- écriture ----
    def create(
        self,
        title: str,
        description: str | None = None,
        priority: str = "medium",
        alert_id: int | None = None,
        created_by: str | None = None,
    ) -> Ticket:
        provider = settings.ITSM_PROVIDER or "internal"
        ticket = Ticket(
            alert_id=alert_id, title=title[:255], description=description,
            priority=priority if priority in PRIORITY_ORDER else "medium",
            provider=provider, created_by=created_by, status="open",
        )
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)

        if provider != "internal":
            from app.core.license import has_feature

            if not has_feature("itsm_connectors"):
                logger.info("Push ITSM (%s) ignoré : plan sans connecteurs ITSM (Business requis)", provider)
                return ticket
            try:
                ext_id, ext_url = self._push(provider, ticket)
                ticket.external_id = ext_id
                ticket.external_url = ext_url
                self.db.commit()
                self.db.refresh(ticket)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Push ITSM (%s) échoué pour ticket #%s : %s", provider, ticket.id, exc)
        return ticket

    def find_open_for_check(self, check_id: int) -> Ticket | None:
        """Ticket encore ouvert (open/in_progress) lié à une alerte de ce check."""
        return self.db.scalar(
            select(Ticket)
            .join(Alert, Alert.id == Ticket.alert_id)
            .where(Alert.check_id == check_id, Ticket.status.in_(("open", "in_progress")))
            .order_by(Ticket.created_at.desc())
        )

    def create_from_alert(
        self, alert: Alert, created_by: str | None = None, dedupe: bool = True
    ) -> Ticket:
        """Crée un ticket depuis un incident. Anti-doublon : si un ticket est déjà
        ouvert pour le même check, on le renvoie au lieu d'en créer un second."""
        if dedupe:
            existing = self.find_open_for_check(alert.check_id)
            if existing:
                # Rattache le ticket à l'alerte la plus récente + trace l'occurrence.
                if existing.alert_id != alert.id:
                    existing.alert_id = alert.id
                    self.db.add(TicketComment(
                        ticket_id=existing.id, author="supervision (auto)",
                        body=(
                            f"⚠️ Nouvelle occurrence de l'incident ({alert.status})"
                            f"{f' : {alert.message}' if alert.message else ''} — "
                            "rattachée à ce ticket (pas de doublon créé)."
                        ),
                    ))
                    self.db.commit()
                    self.db.refresh(existing)
                return existing
        check = self.db.get(Check, alert.check_id)
        check_name = check.name if check else f"check #{alert.check_id}"
        host = None
        if check:
            from app.models.host import Host

            host = self.db.get(Host, check.host_id)
        host_name = host.name if host else "Hôte inconnu"

        # Titre : « Hôte : sujet » (ex. "TDL : Point sur la téléphonie").
        title = f"{host_name} : Incident sur {check_name}"

        # Corps rédigé comme un mail.
        gravite = "critique" if alert.status == "CRITICAL" else "à surveiller"
        detail = f"\n\nDétail technique : {alert.message}" if alert.message else ""
        desc = (
            "Bonjour,\n\n"
            f"Un incident {gravite} est en cours sur l'hôte « {host_name} » : "
            f"le contrôle « {check_name} » est passé en {alert.status}."
            f"{detail}\n\n"
            "Merci de prendre en charge ce ticket.\n\n"
            "Cordialement,\nLa supervision"
        )
        prio = "critical" if alert.status == "CRITICAL" else "high"
        return self.create(title=title, description=desc, priority=prio,
                           alert_id=alert.id, created_by=created_by)

    def resolve_for_check(self, check_id: int) -> int:
        """Passe en 'resolved' les tickets AUTO encore ouverts de ce check
        (appelé quand l'incident se résout). Les tickets manuels sont laissés.

        La raison est journalisée dans les suivis : on doit toujours pouvoir
        comprendre POURQUOI un ticket a été résolu automatiquement."""
        from datetime import datetime

        tickets = list(self.db.scalars(
            select(Ticket)
            .join(Alert, Alert.id == Ticket.alert_id)
            .where(Alert.check_id == check_id,
                   Ticket.status.in_(("open", "in_progress")),
                   Ticket.created_by == "auto")
        ))
        if not tickets:
            return 0
        check = self.db.get(Check, check_id)
        check_name = check.name if check else f"check #{check_id}"
        when = datetime.now().strftime("%d/%m/%Y à %H:%M")
        for t in tickets:
            t.status = "resolved"
            self.db.add(TicketComment(
                ticket_id=t.id, author="supervision (auto)",
                body=(
                    f"✅ Résolu automatiquement le {when} : le contrôle "
                    f"« {check_name} » est repassé à l'état OK — l'incident à "
                    "l'origine de ce ticket est terminé.\n"
                    "Si le problème se reproduit, un nouveau ticket sera ouvert "
                    "automatiquement."
                ),
            ))
        self.db.commit()
        return len(tickets)

    def update_status(self, ticket_id: int, status: str) -> Ticket | None:
        ticket = self.db.get(Ticket, ticket_id)
        if not ticket:
            return None
        if status in STATUSES:
            ticket.status = status
            self.db.commit()
            self.db.refresh(ticket)
        return ticket

    def update(
        self,
        ticket_id: int,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        author: str | None = None,
        assigned_to_id=_UNSET,
    ) -> Ticket | None:
        """Édition complète du ticket (façon GLPI) + suivi automatique des changements."""
        ticket = self.db.get(Ticket, ticket_id)
        if not ticket:
            return None
        changes: list[str] = []
        if assigned_to_id is not _UNSET and assigned_to_id != ticket.assigned_to_id:
            from app.models.user import User

            if assigned_to_id is None:
                changes.append("ticket désassigné")
                ticket.assigned_to_id = None
            else:
                target = self.db.get(User, assigned_to_id)
                if target:
                    changes.append(f"assigné à {target.email}")
                    ticket.assigned_to_id = target.id
                    self._notify_assignee(ticket, target, author)
        if title is not None and title.strip() and title != ticket.title:
            changes.append(f"titre : « {ticket.title} » → « {title.strip()[:255]} »")
            ticket.title = title.strip()[:255]
        if description is not None and description != ticket.description:
            changes.append("description modifiée")
            ticket.description = description
        if priority is not None and priority in PRIORITY_ORDER and priority != ticket.priority:
            changes.append(f"priorité : {ticket.priority} → {priority}")
            ticket.priority = priority
        if status is not None and status in STATUSES and status != ticket.status:
            changes.append(f"statut : {ticket.status} → {status}")
            ticket.status = status
        if changes:
            # Journalise la modification dans le fil de suivis (historique GLPI-like).
            self.db.add(TicketComment(
                ticket_id=ticket.id, author=author or "système",
                body="✏️ Modification : " + " ; ".join(changes),
            ))
            self.db.commit()
            self.db.refresh(ticket)
        return ticket

    def _notify_assignee(self, ticket: Ticket, target, author: str | None) -> None:
        """E-mail à l'assigné (best-effort : n'échoue jamais l'assignation).

        Ne notifie pas quand on s'assigne le ticket à soi-même."""
        if author and target.email == author:
            return
        try:
            from app.notifications.base import Notification
            from app.notifications.email_notifier import EmailNotifier

            tasks_open = sum(1 for t in ticket.tasks if not t.done)
            body = (
                "Bonjour,\n\n"
                f"Le ticket #{ticket.id} « {ticket.title} » vous a été assigné"
                f"{f' par {author}' if author else ''}.\n\n"
                f"Priorité : {ticket.priority} · Statut : {ticket.status}"
                f"{f' · {tasks_open} tâche(s) à faire' if tasks_open else ''}\n\n"
                f"{(ticket.description or '')[:500]}\n\n"
                "Cordialement,\nLa supervision"
            )
            sent = EmailNotifier().send(
                Notification(
                    subject=f"[Ticket #{ticket.id}] {ticket.title}",
                    body=body, status=ticket.status,
                    check_name=f"ticket #{ticket.id}", host_name="",
                ),
                {"to": target.email},
            )
            if sent:
                logger.info("Assignation du ticket #%s notifiée à %s", ticket.id, target.email)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Notification d'assignation échouée : %s", exc)

    # ---- suivis (commentaires) ----
    def add_comment(self, ticket_id: int, body: str, author: str | None = None) -> TicketComment | None:
        if not self.db.get(Ticket, ticket_id):
            return None
        comment = TicketComment(ticket_id=ticket_id, body=body, author=author)
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def delete_comment(self, comment_id: int) -> bool:
        comment = self.db.get(TicketComment, comment_id)
        if not comment:
            return False
        self.db.delete(comment)
        self.db.commit()
        return True

    def delete(self, ticket_id: int) -> bool:
        ticket = self.db.get(Ticket, ticket_id)
        if not ticket:
            return False
        self.db.delete(ticket)
        self.db.commit()
        return True

    # ---- tâches (checklist) ----
    def add_task(self, ticket_id: int, label: str) -> TicketTask | None:
        ticket = self.db.get(Ticket, ticket_id)
        if not ticket:
            return None
        pos = max((t.position for t in ticket.tasks), default=-1) + 1
        task = TicketTask(ticket_id=ticket_id, label=label[:255], position=pos)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_task(self, task_id: int, done: bool | None = None, label: str | None = None) -> TicketTask | None:
        task = self.db.get(TicketTask, task_id)
        if not task:
            return None
        if done is not None:
            task.done = done
        if label is not None:
            task.label = label[:255]
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete_task(self, task_id: int) -> bool:
        task = self.db.get(TicketTask, task_id)
        if not task:
            return False
        self.db.delete(task)
        self.db.commit()
        return True

    # ---- adapters externes ----
    def _push(self, provider: str, ticket: Ticket) -> tuple[str | None, str | None]:
        if provider == "webhook":
            return self._push_webhook(ticket)
        if provider == "jira":
            return self._push_jira(ticket)
        if provider == "servicenow":
            return self._push_servicenow(ticket)
        return None, None

    def _push_webhook(self, ticket: Ticket) -> tuple[str | None, str | None]:
        payload = {
            "title": ticket.title, "description": ticket.description,
            "priority": ticket.priority, "source": "opsora",
            "alert_id": ticket.alert_id,
        }
        r = httpx.post(settings.ITSM_URL, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        return str(data.get("id") or data.get("ticket_id") or ""), data.get("url")

    def _basic_auth(self, user: str) -> dict:
        raw = f"{user}:{settings.ITSM_TOKEN}".encode()
        return {"Authorization": "Basic " + base64.b64encode(raw).decode()}

    def _push_jira(self, ticket: Ticket) -> tuple[str | None, str | None]:
        url = settings.ITSM_URL.rstrip("/") + "/rest/api/2/issue"
        body = {
            "fields": {
                "project": {"key": settings.ITSM_PROJECT},
                "summary": ticket.title,
                "description": ticket.description or "",
                "issuetype": {"name": "Bug"},
            }
        }
        r = httpx.post(url, json=body, headers=self._basic_auth(settings.ITSM_USER), timeout=10)
        r.raise_for_status()
        key = r.json().get("key")
        return key, (settings.ITSM_URL.rstrip("/") + f"/browse/{key}" if key else None)

    def _push_servicenow(self, ticket: Ticket) -> tuple[str | None, str | None]:
        table = settings.ITSM_PROJECT or "incident"
        url = settings.ITSM_URL.rstrip("/") + f"/api/now/table/{table}"
        body = {"short_description": ticket.title, "description": ticket.description or ""}
        r = httpx.post(url, json=body, headers=self._basic_auth(settings.ITSM_USER), timeout=10)
        r.raise_for_status()
        res = r.json().get("result", {})
        return res.get("number"), res.get("sys_id")
