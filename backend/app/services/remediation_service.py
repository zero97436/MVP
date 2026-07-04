"""Remédiation semi-automatique (Niveau 1).

Liste blanche d'actions sûres, exécutables UNIQUEMENT après validation humaine
(rôle opérateur/admin). Chaque exécution est journalisée (RemediationLog).
L'IA peut *suggérer* une action, mais ne l'exécute jamais d'elle-même.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.alert import Alert
from app.models.check import Check
from app.models.notification_channel import NotificationChannel
from app.models.remediation_log import RemediationLog

logger = get_logger(__name__)


@dataclass
class RemediationAction:
    id: str
    label: str
    description: str
    executor: Callable[["RemediationService", Alert], tuple[str, str]]


class RemediationService:
    def __init__(self, db: Session):
        self.db = db

    # --- Catalogue (liste blanche) ---
    @property
    def actions(self) -> dict[str, RemediationAction]:
        return {
            a.id: a
            for a in [
                RemediationAction(
                    "rerun_check",
                    "Relancer le check",
                    "Ré-exécute la sonde immédiatement (résout les incidents transitoires).",
                    RemediationService._do_rerun,
                ),
                RemediationAction(
                    "acknowledge",
                    "Acquitter l'incident",
                    "Marque l'incident comme pris en charge.",
                    RemediationService._do_ack,
                ),
                RemediationAction(
                    "escalate",
                    "Escalader (notifier)",
                    "Envoie une notification à tous les canaux actifs.",
                    RemediationService._do_escalate,
                ),
                RemediationAction(
                    "agent_top_processes",
                    "Diagnostic agent : top processus",
                    "Demande à l'agent de l'hôte la liste des processus les plus gourmands (lecture seule).",
                    RemediationService._do_agent_top_processes,
                ),
            ]
        }

    def available(self) -> list[dict]:
        return [
            {"id": a.id, "label": a.label, "description": a.description}
            for a in self.actions.values()
        ]

    def suggest(self, alert: Alert) -> str:
        """Suggestion par défaut (repli si l'IA ne propose rien)."""
        return "rerun_check"

    # --- Exécution (validée par un humain) ---
    def execute(self, alert_id: int, action_id: str, user_email: str) -> dict | None:
        alert = self.db.get(Alert, alert_id)
        if not alert:
            return None
        action = self.actions.get(action_id)
        if not action:
            raise ValueError(f"Action inconnue ou non autorisée : {action_id}")

        self._user_email = user_email
        extra: dict = {}
        try:
            res = action.executor(self, alert)
            if len(res) == 3:
                status, detail, extra = res  # type: ignore[misc]
            else:
                status, detail = res  # type: ignore[misc]
        except Exception as exc:  # noqa: BLE001
            status, detail = "failed", str(exc)
            logger.error("Remediation '%s' failed: %s", action_id, exc)

        self.db.add(
            RemediationLog(
                alert_id=alert_id,
                action=action_id,
                status=status,
                detail=detail,
                params=extra or None,
                performed_by=user_email,
            )
        )
        self.db.commit()

        from app.services.event_service import EventService

        EventService(self.db).record(
            "remediation",
            f"Remédiation '{action_id}' → {status} : {detail}",
            level="info" if status == "success" else "warning",
            check_id=alert.check_id,
            actor=user_email,
        )
        return {"action": action_id, "status": status, "detail": detail, **extra}

    def history(self, alert_id: int) -> list[RemediationLog]:
        return list(
            self.db.scalars(
                select(RemediationLog)
                .where(RemediationLog.alert_id == alert_id)
                .order_by(RemediationLog.created_at.desc())
            )
        )

    # --- Exécuteurs ---
    def _do_rerun(self, alert: Alert) -> tuple[str, str]:
        from app.services.check_service import CheckService

        result = CheckService(self.db).run_check_by_id(alert.check_id)
        if result is None:
            return "failed", "Check introuvable"
        return "success", f"Check relancé → statut {result['status']}"

    def _do_ack(self, alert: Alert) -> tuple[str, str]:
        from app.services.dashboard_service import DashboardService

        DashboardService(self.db).acknowledge(alert.id, "remediation", ack=True)
        return "success", "Incident acquitté"

    def _do_escalate(self, alert: Alert) -> tuple[str, str]:
        from app.notifications import get_notifier
        from app.notifications.base import Notification

        check = self.db.get(Check, alert.check_id)
        channels = list(
            self.db.scalars(
                select(NotificationChannel).where(NotificationChannel.is_active.is_(True))
            )
        )
        if not channels:
            return "failed", "Aucun canal de notification actif"
        notif = Notification(
            subject=f"[ESCALADE] {alert.status}",
            body=alert.message or "Incident escaladé manuellement.",
            status=alert.status,
            check_name=check.name if check else "—",
            host_name=check.host.name if check and check.host else "—",
        )
        from app.core.crypto import decrypt_config

        sent = 0
        for ch in channels:
            notifier = get_notifier(ch.type)
            if notifier and notifier.send(notif, decrypt_config(ch.config_json or {})):
                sent += 1
        return ("success" if sent else "failed"), f"Notifié {sent}/{len(channels)} canal(aux)"

    def _do_agent_top_processes(self, alert: Alert) -> tuple[str, str, dict]:
        from app.models.agent_command import AgentCommand

        check = self.db.get(Check, alert.check_id)
        if not check:
            return "failed", "Check introuvable", {}
        cmd = AgentCommand(
            host_id=check.host_id,
            action="top_processes",
            status="pending",
            requested_by=getattr(self, "_user_email", None),
        )
        self.db.add(cmd)
        self.db.flush()  # pour obtenir l'id avant le commit global
        return (
            "success",
            f"Commande envoyée à l'agent (en attente d'exécution, id {cmd.id})",
            {"command_id": cmd.id},
        )
