"""Check ping : envoie un ping ICMP via la commande système."""
import platform
import subprocess

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus


class PingCheck(BaseCheck):
    type = "ping"

    def run(self, ctx: CheckContext) -> CheckResultData:
        count = str(ctx.config.get("count", 2))
        is_windows = platform.system().lower() == "windows"
        count_flag = "-n" if is_windows else "-c"
        timeout_flag = "-w" if is_windows else "-W"
        # Sous Windows le timeout est en ms, sous Linux en secondes.
        timeout_val = str(ctx.timeout_seconds * 1000) if is_windows else str(ctx.timeout_seconds)

        cmd = ["ping", count_flag, count, timeout_flag, timeout_val, ctx.hostname_or_ip]
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=ctx.timeout_seconds + 5
        )

        if proc.returncode == 0:
            return CheckResultData(
                status=CheckStatus.OK,
                message=f"Host {ctx.hostname_or_ip} is reachable",
                perfdata={"returncode": 0},
            )
        return CheckResultData(
            status=CheckStatus.CRITICAL,
            message=f"Host {ctx.hostname_or_ip} unreachable (rc={proc.returncode})",
            perfdata={"returncode": proc.returncode},
        )
