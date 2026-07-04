"""Check ssh : vérifie qu'un service SSH répond (bannière SSH-)."""
from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.checks.plugins._banner import grab_banner
from app.models.enums import CheckStatus


class SshCheck(BaseCheck):
    type = "ssh"

    def run(self, ctx: CheckContext) -> CheckResultData:
        port = int(ctx.config.get("port", 22))
        try:
            banner, ms = grab_banner(ctx.hostname_or_ip, port, ctx.timeout_seconds)
        except OSError as exc:
            return CheckResultData(status=CheckStatus.CRITICAL, message=f"SSH injoignable: {exc}")
        if banner.startswith("SSH-"):
            return CheckResultData(
                status=CheckStatus.OK, value=float(ms),
                message=f"SSH OK ({banner.splitlines()[0][:60]}) en {ms} ms",
                perfdata={"response_ms": ms, "port": port},
            )
        return CheckResultData(status=CheckStatus.CRITICAL, message=f"Pas de bannière SSH (port {port})")
