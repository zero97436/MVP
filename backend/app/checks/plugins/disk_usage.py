"""Check disk_usage.

MVP : aucun agent distant n'est encore déployé sur les hôtes supervisés.
Deux modes honnêtes :
  - mode "mock" (config_json.mock=true) : valeur simulée, message explicite.
  - sinon : UNKNOWN avec un message clair indiquant qu'un agent est requis.
On ne fait PAS semblant de collecter une vraie métrique distante.
"""
import random

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus


class DiskUsageCheck(BaseCheck):
    type = "disk_usage"

    def run(self, ctx: CheckContext) -> CheckResultData:
        if not ctx.config.get("mock"):
            return CheckResultData(
                status=CheckStatus.UNKNOWN,
                message=(
                    "disk_usage requires an agent on the host (not yet deployed). "
                    "Set config_json.mock=true to simulate."
                ),
            )

        used = ctx.config.get("mock_value", random.randint(40, 95))
        warn = ctx.warning_threshold if ctx.warning_threshold is not None else 80
        crit = ctx.critical_threshold if ctx.critical_threshold is not None else 90

        if used >= crit:
            status = CheckStatus.CRITICAL
        elif used >= warn:
            status = CheckStatus.WARNING
        else:
            status = CheckStatus.OK

        return CheckResultData(
            status=status,
            value=float(used),
            message=f"[MOCK] Disk usage at {used}%",
            perfdata={"used_percent": used, "mock": True},
        )
