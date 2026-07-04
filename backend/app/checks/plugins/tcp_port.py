"""Check tcp_port : vérifie qu'un port TCP est ouvert."""
import socket
import time

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus


class TcpPortCheck(BaseCheck):
    type = "tcp_port"

    def run(self, ctx: CheckContext) -> CheckResultData:
        port = ctx.config.get("port")
        if not port:
            return CheckResultData(
                status=CheckStatus.UNKNOWN,
                message="config_json.port is required",
            )

        start = time.perf_counter()
        try:
            with socket.create_connection(
                (ctx.hostname_or_ip, int(port)), timeout=ctx.timeout_seconds
            ):
                elapsed_ms = (time.perf_counter() - start) * 1000
                return CheckResultData(
                    status=CheckStatus.OK,
                    value=round(elapsed_ms, 1),
                    message=f"Port {port} open ({elapsed_ms:.0f} ms)",
                    perfdata={"connect_ms": round(elapsed_ms, 1), "port": int(port)},
                )
        except (OSError, ValueError) as exc:
            return CheckResultData(
                status=CheckStatus.CRITICAL,
                message=f"Port {port} closed/unreachable: {exc}",
                perfdata={"port": port},
            )
