"""Check imap : vérifie qu'un serveur IMAP répond (bannière '* OK')."""
from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.checks.plugins._banner import grab_banner
from app.models.enums import CheckStatus


class ImapCheck(BaseCheck):
    type = "imap"

    def run(self, ctx: CheckContext) -> CheckResultData:
        port = int(ctx.config.get("port", 143))
        try:
            banner, ms = grab_banner(ctx.hostname_or_ip, port, ctx.timeout_seconds)
        except OSError as exc:
            return CheckResultData(status=CheckStatus.CRITICAL, message=f"IMAP injoignable: {exc}")
        if banner.startswith("* OK"):
            return CheckResultData(
                status=CheckStatus.OK, value=float(ms),
                message=f"IMAP OK en {ms} ms", perfdata={"response_ms": ms, "port": port},
            )
        return CheckResultData(status=CheckStatus.CRITICAL, message=f"Réponse IMAP inattendue (port {port}): {banner[:60]}")
