"""Interface commune à tous les checks (plugins)."""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.models.enums import CheckStatus


@dataclass
class CheckContext:
    """Données passées au check au moment de l'exécution."""
    hostname_or_ip: str
    timeout_seconds: int
    warning_threshold: float | None
    critical_threshold: float | None
    config: dict[str, Any] = field(default_factory=dict)
    # Optionnels : utiles aux checks qui lisent l'état stocké (ex. métriques agent,
    # compteurs SNMP qui nécessitent le relevé précédent).
    host_id: int | None = None
    check_id: int | None = None
    db: Any = None


@dataclass
class CheckResultData:
    """Format de sortie standard d'un check."""
    status: CheckStatus
    message: str
    value: float | None = None
    perfdata: dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "value": self.value,
            "message": self.message,
            "perfdata": self.perfdata,
            "checked_at": self.checked_at.isoformat(),
            "duration_ms": self.duration_ms,
        }


class BaseCheck(ABC):
    """Tout check concret hérite de cette classe et implémente `run`."""

    type: str = "base"

    @abstractmethod
    def run(self, ctx: CheckContext) -> CheckResultData:  # pragma: no cover
        ...

    def execute(self, ctx: CheckContext) -> CheckResultData:
        """Wrapper qui mesure la durée et capture les exceptions."""
        start = time.perf_counter()
        try:
            result = self.run(ctx)
        except Exception as exc:  # noqa: BLE001 - on normalise toute erreur en UNKNOWN
            result = CheckResultData(
                status=CheckStatus.UNKNOWN,
                message=f"Check error: {exc}",
            )
        result.duration_ms = int((time.perf_counter() - start) * 1000)
        return result
