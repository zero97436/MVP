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
                message="Port manquant : renseignez le port dans la configuration "
                        '(config_json : {"port": 443}).',
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
            reason = str(exc)
            low = reason.lower()
            if "timed out" in low or "timeout" in low:
                hint = f"aucune réponse (pare-feu bloquant, ou {ctx.hostname_or_ip} injoignable ?)"
            elif "refused" in low:
                hint = "connexion refusée (le service n'écoute pas sur ce port)"
            elif "name or service" in low or "resolve" in low or "getaddrinfo" in low:
                hint = f"nom « {ctx.hostname_or_ip} » non résolu (DNS/hostname incorrect ?)"
            else:
                hint = reason
            return CheckResultData(
                status=CheckStatus.CRITICAL,
                message=f"Port {port} sur {ctx.hostname_or_ip} injoignable : {hint}",
                perfdata={"port": int(port) if str(port).isdigit() else port},
            )
