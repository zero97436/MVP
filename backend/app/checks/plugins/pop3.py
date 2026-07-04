"""Check pop3 : vérifie qu'un serveur POP3 répond (bannière '+OK')."""
from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.checks.plugins._banner import grab_banner
from app.models.enums import CheckStatus


class Pop3Check(BaseCheck):
    type = "pop3"

    def run(self, ctx: CheckContext) -> CheckResultData:
        port = int(ctx.config.get("port", 110))
        try:
            banner, ms = grab_banner(ctx.hostname_or_ip, port, ctx.timeout_seconds)
        except OSError as exc:
            return CheckResultData(status=CheckStatus.CRITICAL, message=f"POP3 injoignable: {exc}")
        if banner.startswith("+OK"):
            return CheckResultData(
                status=CheckStatus.OK, value=float(ms),
                message=f"POP3 OK en {ms} ms", perfdata={"response_ms": ms, "port": port},
            )
        return CheckResultData(status=CheckStatus.CRITICAL, message=f"Réponse POP3 inattendue (port {port}): {banner[:60]}")
