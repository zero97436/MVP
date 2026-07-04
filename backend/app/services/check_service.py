"""Exécution d'un check : lance le plugin, stocke le résultat, déclenche l'alerting."""
from sqlalchemy.orm import Session

from app.checks.base import CheckContext
from app.checks.registry import get_check
from app.core.crypto import decrypt_config
from app.core.logging import get_logger
from app.models.check import Check
from app.models.enums import CheckStatus
from app.repositories.check_repo import CheckRepository
from app.services.alert_service import AlertService

logger = get_logger(__name__)


class CheckService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CheckRepository(db)
        self.alert_service = AlertService(db)

    def run_check(self, check: Check) -> dict:
        plugin = get_check(check.type)
        if plugin is None:
            logger.warning("No plugin for check type '%s'", check.type)
            result_data = _unknown(f"Unsupported check type: {check.type}")
        else:
            ctx = CheckContext(
                hostname_or_ip=check.host.hostname_or_ip,
                timeout_seconds=check.timeout_seconds,
                warning_threshold=check.warning_threshold,
                critical_threshold=check.critical_threshold,
                config=decrypt_config(check.config_json or {}),
                host_id=check.host_id,
                check_id=check.id,
                db=self.db,
            )
            result_data = plugin.execute(ctx)

        # Persistance du résultat.
        self.repo.add_result(
            check_id=check.id,
            status=result_data.status.value,
            value=result_data.value,
            message=result_data.message,
            perfdata=result_data.perfdata,
            duration_ms=result_data.duration_ms,
            checked_at=result_data.checked_at,
        )

        # Alerting sur changement d'état.
        previous = check.last_status
        self.alert_service.handle_status_change(
            check, result_data.status.value, previous, result_data.message
        )

        # Mise à jour du dernier statut.
        check.last_status = result_data.status.value
        self.db.commit()

        logger.info(
            "Check #%s (%s) -> %s (%dms)",
            check.id, check.type, result_data.status.value, result_data.duration_ms,
        )
        return result_data.to_dict()

    def run_check_by_id(self, check_id: int) -> dict | None:
        check = self.repo.get(check_id)
        if not check:
            return None
        return self.run_check(check)

    def ingest_external_result(
        self,
        check: Check,
        status: str,
        value: float | None,
        message: str | None,
        perfdata: dict | None,
        duration_ms: int | None,
    ) -> None:
        """Enregistre un résultat produit par un AGENT-SONDE (poller distant) :
        persiste, déclenche l'alerting, met à jour le dernier statut."""
        from datetime import datetime, timezone

        self.repo.add_result(
            check_id=check.id,
            status=status,
            value=value,
            message=message,
            perfdata=perfdata,
            duration_ms=duration_ms,
            checked_at=datetime.now(timezone.utc),
        )
        previous = check.last_status
        self.alert_service.handle_status_change(check, status, previous, message)
        check.last_status = status
        self.db.commit()
        logger.info("Check #%s (%s) [agent] -> %s", check.id, check.type, status)


def _unknown(message: str):
    from app.checks.base import CheckResultData
    return CheckResultData(status=CheckStatus.UNKNOWN, message=message)
