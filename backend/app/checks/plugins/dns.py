"""Check dns : interroge le serveur DNS (hostname_or_ip) pour résoudre un nom.

config_json :
  - name   : nom à résoudre (défaut 'example.com')
  - record : type d'enregistrement (défaut 'A')
"""
import time

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus


class DnsCheck(BaseCheck):
    type = "dns"

    def run(self, ctx: CheckContext) -> CheckResultData:
        name = ctx.config.get("name", "example.com")
        record = ctx.config.get("record", "A")
        try:
            import dns.resolver  # fourni par dnspython (dépendance d'email-validator)
        except ImportError:
            return CheckResultData(status=CheckStatus.UNKNOWN, message="dnspython non installé")

        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = [ctx.hostname_or_ip]
        resolver.lifetime = ctx.timeout_seconds
        resolver.timeout = ctx.timeout_seconds

        t0 = time.time()
        try:
            answer = resolver.resolve(name, record)
        except Exception as exc:  # noqa: BLE001  (dns.exception.*)
            return CheckResultData(
                status=CheckStatus.CRITICAL,
                message=f"Résolution {record} '{name}' échouée : {type(exc).__name__}",
            )
        ms = int((time.time() - t0) * 1000)
        values = [r.to_text() for r in answer]
        return CheckResultData(
            status=CheckStatus.OK, value=float(ms),
            message=f"{name} {record} → {', '.join(values)[:80]} ({ms} ms)",
            perfdata={"response_ms": ms, "records": len(values)},
        )
