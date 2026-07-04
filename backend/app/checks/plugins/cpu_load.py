"""Check cpu_load.

Même logique que disk_usage : nécessite un agent distant non encore déployé.
Mode mock explicite, sinon UNKNOWN honnête.
"""
import random

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus


class CpuLoadCheck(BaseCheck):
    type = "cpu_load"

    def run(self, ctx: CheckContext) -> CheckResultData:
        if not ctx.config.get("mock"):
            return CheckResultData(
                status=CheckStatus.UNKNOWN,
                message=(
                    "cpu_load requires an agent on the host (not yet deployed). "
                    "Set config_json.mock=true to simulate."
                ),
            )

        load = ctx.config.get("mock_value", round(random.uniform(0.1, 4.0), 2))
        warn = ctx.warning_threshold if ctx.warning_threshold is not None else 2.0
        crit = ctx.critical_threshold if ctx.critical_threshold is not None else 4.0

        if load >= crit:
            status = CheckStatus.CRITICAL
        elif load >= warn:
            status = CheckStatus.WARNING
        else:
            status = CheckStatus.OK

        return CheckResultData(
            status=status,
            value=float(load),
            message=f"[MOCK] CPU load (1m) at {load}",
            perfdata={"load1": load, "mock": True},
        )
