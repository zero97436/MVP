"""Check http : requête GET, vérifie le code HTTP et mesure le temps de réponse."""
import httpx

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus


class HttpCheck(BaseCheck):
    type = "http"

    def run(self, ctx: CheckContext) -> CheckResultData:
        cfg = ctx.config
        # URL explicite ou reconstruite à partir de l'hôte.
        url = cfg.get("url")
        if not url:
            scheme = cfg.get("scheme", "http")
            path = cfg.get("path", "/")
            port = cfg.get("port")
            host = f"{ctx.hostname_or_ip}:{port}" if port else ctx.hostname_or_ip
            url = f"{scheme}://{host}{path}"

        expected = int(cfg.get("expected_status", 200))

        resp = httpx.get(url, timeout=ctx.timeout_seconds, follow_redirects=True)
        elapsed_ms = resp.elapsed.total_seconds() * 1000
        perfdata = {"status_code": resp.status_code, "response_ms": round(elapsed_ms, 1)}

        if resp.status_code != expected:
            return CheckResultData(
                status=CheckStatus.CRITICAL,
                value=round(elapsed_ms, 1),
                message=f"HTTP {resp.status_code} (expected {expected}) at {url}",
                perfdata=perfdata,
            )

        # Seuils optionnels sur le temps de réponse (ms).
        status = CheckStatus.OK
        if ctx.critical_threshold is not None and elapsed_ms >= ctx.critical_threshold:
            status = CheckStatus.CRITICAL
        elif ctx.warning_threshold is not None and elapsed_ms >= ctx.warning_threshold:
            status = CheckStatus.WARNING

        return CheckResultData(
            status=status,
            value=round(elapsed_ms, 1),
            message=f"HTTP {resp.status_code} in {elapsed_ms:.0f} ms",
            perfdata=perfdata,
        )
