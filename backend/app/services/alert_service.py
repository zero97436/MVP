"""Gestion des alertes : génération sur changement d'état + notifications.

Règles :
  - une alerte est créée quand un check passe en WARNING/CRITICAL ET que l'état
    a changé (évite le spam si l'état reste identique).
  - quand un check repasse OK, l'alerte active est résolue.
"""
from datetime import datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.alert import Alert
from app.models.check import Check
from app.models.enums import CheckStatus
from app.models.notification_channel import NotificationChannel
from app.notifications import get_notifier
from app.notifications.base import Notification

logger = get_logger(__name__)

ALERTING_STATUSES = {CheckStatus.WARNING.value, CheckStatus.CRITICAL.value}


def _in_active_hours(window: str | None) -> bool:
    """Vrai si l'heure courante est dans 'HH:MM-HH:MM' (gère le passage minuit).
    Vide/invalide -> 24/7."""
    if not window:
        return True
    try:
        start_s, end_s = window.split("-")
        sh, sm = map(int, start_s.strip().split(":"))
        eh, em = map(int, end_s.strip().split(":"))
        start, end = time(sh, sm), time(eh, em)
    except (ValueError, AttributeError):
        return True
    now = datetime.now().time()
    if start <= end:
        return start <= now <= end
    return now >= start or now <= end  # plage à cheval sur minuit


class AlertService:
    def __init__(self, db: Session):
        self.db = db

    def handle_status_change(
        self, check: Check, new_status: str, previous_status: str | None, message: str
    ) -> None:
        if new_status == previous_status:
            return  # pas de changement -> rien à faire

        if new_status in ALERTING_STATUSES:
            from app.services.maintenance_service import MaintenanceService

            if MaintenanceService(self.db).is_in_maintenance(check):
                logger.info("Check #%s en maintenance -> alerte supprimée", check.id)
                self._event(
                    "alert_suppressed", f"{check.name} {new_status} (en maintenance)",
                    check, level="info",
                )
                return
            if self._ancestor_down(check):
                logger.info("Check #%s : hôte parent en panne -> alerte supprimée", check.id)
                self._event(
                    "alert_suppressed_dependency",
                    f"{check.name} {new_status} (hôte parent en panne)", check, level="info",
                )
                return
            if self._is_flapping(check):
                logger.info("Check #%s en flapping -> alerte supprimée", check.id)
                self._event(
                    "alert_suppressed_flapping",
                    f"{check.name} {new_status} (flapping : état instable, alertes suspendues)",
                    check, level="warning",
                )
                return
            self._open_alert(check, new_status, previous_status, message)
        elif new_status == CheckStatus.OK.value:
            self._resolve_alerts(check)

    def _open_alert(self, check, new_status, previous_status, message) -> None:
        alert = Alert(
            check_id=check.id,
            status=new_status,
            previous_status=previous_status,
            message=message,
            is_active=True,
        )
        self.db.add(alert)
        self.db.commit()
        logger.info("Alert opened for check #%s -> %s", check.id, new_status)
        self._event(
            "alert_opened", f"{check.name} : {new_status} — {message or ''}".strip(),
            check, level="critical" if new_status == CheckStatus.CRITICAL.value else "warning",
        )
        self._dispatch(check, new_status, message)
        self._maybe_open_ticket(alert, new_status)

    def _maybe_open_ticket(self, alert, new_status) -> None:
        """Ouvre automatiquement un ticket ITSM si activé (CRITICAL et WARNING).

        Anti-doublon : si un ticket est déjà ouvert pour le même check, il est
        réutilisé (aucun second ticket créé, même en cas de flapping)."""
        from app.core.config import settings

        if not settings.ITSM_AUTO_CREATE:
            return
        if new_status not in (CheckStatus.CRITICAL.value, CheckStatus.WARNING.value):
            return
        try:
            from app.services.ticket_service import TicketService

            ticket = TicketService(self.db).create_from_alert(alert, created_by="auto")
            logger.info("Ticket #%s lié à l'alerte #%s (auto)", ticket.id, alert.id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Auto-création ticket ITSM échouée : %s", exc)

    def _resolve_alerts(self, check) -> None:
        active = self.db.scalars(
            select(Alert).where(Alert.check_id == check.id, Alert.is_active.is_(True))
        ).all()
        for alert in active:
            alert.is_active = False
            alert.resolved_at = datetime.now(timezone.utc)
        if active:
            self.db.commit()
            logger.info("Resolved %d alert(s) for check #%s", len(active), check.id)
            self._event("alert_resolved", f"{check.name} : retour OK", check, level="info")
            # Résout aussi les tickets AUTO liés à ce check (les manuels restent).
            try:
                from app.services.ticket_service import TicketService

                n = TicketService(self.db).resolve_for_check(check.id)
                if n:
                    logger.info("%d ticket(s) auto résolus pour check #%s", n, check.id)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Auto-résolution tickets échouée : %s", exc)

    def _is_flapping(self, check) -> bool:
        """Vrai si le check oscille : trop de changements d'état sur la fenêtre
        des N derniers résultats (à la Nagios). Évite les tempêtes d'alertes."""
        from app.core.config import settings

        if not settings.FLAPPING_ENABLED:
            return False
        from app.models.check_result import CheckResult

        results = self.db.scalars(
            select(CheckResult)
            .where(CheckResult.check_id == check.id)
            .order_by(CheckResult.checked_at.desc())
            .limit(settings.FLAPPING_WINDOW)
        ).all()
        if len(results) < settings.FLAPPING_WINDOW // 2:
            return False  # pas assez d'historique pour juger
        statuses = [r.status for r in reversed(results)]
        transitions = sum(1 for a, b in zip(statuses, statuses[1:]) if a != b)
        return transitions >= settings.FLAPPING_THRESHOLD

    def _ancestor_down(self, check) -> bool:
        """Vrai si un hôte ancêtre (parent, grand-parent…) est en panne (CRITICAL)."""
        from app.models.host import Host

        host = self.db.get(Host, check.host_id)
        seen: set[int] = set()
        parent_id = host.parent_host_id if host else None
        while parent_id and parent_id not in seen and len(seen) < 10:
            seen.add(parent_id)
            parent = self.db.get(Host, parent_id)
            if not parent:
                break
            statuses = [c.last_status or "UNKNOWN" for c in parent.checks]
            if "CRITICAL" in statuses:
                return True
            parent_id = parent.parent_host_id
        return False

    def _event(self, etype: str, message: str, check, level: str = "info") -> None:
        from app.services.event_service import EventService

        EventService(self.db).record(
            etype, message, level=level, host_id=check.host_id, check_id=check.id,
        )

    def _dispatch(self, check, status, message, escalation: bool = False) -> None:
        from app.core.crypto import decrypt_config

        all_channels = self.db.scalars(
            select(NotificationChannel).where(NotificationChannel.is_active.is_(True))
        ).all()
        if not all_channels:
            return

        if escalation:
            # Escalade -> canaux "astreinte" (escalation_only) ; sinon repli sur tous.
            channels = [c for c in all_channels if c.escalation_only] or all_channels
        else:
            channels = [c for c in all_channels if not c.escalation_only]
        channels = [c for c in channels if _in_active_hours(c.active_hours)]
        if not channels:
            return

        host_name = check.host.name if check.host else "unknown"
        prefix = "[ESCALADE] " if escalation else ""
        notif = Notification(
            subject=f"{prefix}[{status}] {host_name} / {check.name}",
            body=message or "",
            status=status,
            check_name=check.name,
            host_name=host_name,
        )
        for channel in channels:
            notifier = get_notifier(channel.type)
            if notifier:
                notifier.send(notif, decrypt_config(channel.config_json or {}))

    def escalate_pending(self) -> int:
        """Escalade les alertes actives non acquittées depuis trop longtemps (1 fois)."""
        from app.core.config import settings

        if not settings.ESCALATION_ENABLED:
            return 0
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.ESCALATION_AFTER_MINUTES)
        alerts = self.db.scalars(
            select(Alert).where(
                Alert.is_active.is_(True),
                Alert.acknowledged.is_(False),
                Alert.escalated_at.is_(None),
                Alert.created_at <= cutoff,
            )
        ).all()
        count = 0
        for alert in alerts:
            check = self.db.get(Check, alert.check_id)
            if not check:
                continue
            self._dispatch(check, alert.status, alert.message or "", escalation=True)
            alert.escalated_at = datetime.now(timezone.utc)
            self.db.commit()
            self._event("alert_escalated", f"{check.name} : escaladé (non acquitté)", check, level="warning")
            count += 1
        return count
