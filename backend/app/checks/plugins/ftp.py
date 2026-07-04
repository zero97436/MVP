"""Check ftp : vérifie qu'un serveur FTP répond (code 220)."""
from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.checks.plugins._banner import grab_banner
from app.models.enums import CheckStatus


class FtpCheck(BaseCheck):
    type = "ftp"

    def run(self, ctx: CheckContext) -> CheckResultData:
        port = int(ctx.config.get("port", 21))
        try:
            banner, ms = grab_banner(ctx.hostname_or_ip, port, ctx.timeout_seconds)
        except OSError as exc:
            return CheckResultData(status=CheckStatus.CRITICAL, message=f"FTP injoignable: {exc}")
        if banner.startswith("220"):
            return CheckResultData(
                status=CheckStatus.OK, value=float(ms),
                message=f"FTP OK en {ms} ms", perfdata={"response_ms": ms, "port": port},
            )
        return CheckResultData(status=CheckStatus.CRITICAL, message=f"Réponse FTP inattendue (port {port}): {banner[:60]}")
