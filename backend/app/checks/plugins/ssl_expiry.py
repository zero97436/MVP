"""Check ssl_expiry : récupère le certificat TLS et vérifie sa date d'expiration.

config_json :
  - port      : port TLS (défaut 443)
  - insecure  : true pour accepter un certificat auto-signé / non vérifié
                (lit quand même la date d'expiration). Utile pour les équipements
                réseau (box, routeur) qui présentent un certificat auto-signé.
"""
import socket
import ssl
from datetime import datetime, timezone

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus


class SslExpiryCheck(BaseCheck):
    type = "ssl_expiry"

    def run(self, ctx: CheckContext) -> CheckResultData:
        port = int(ctx.config.get("port", 443))
        insecure = bool(ctx.config.get("insecure", False))
        warn_days = ctx.warning_threshold if ctx.warning_threshold is not None else 30
        crit_days = ctx.critical_threshold if ctx.critical_threshold is not None else 7

        not_after = self._read_not_after(ctx, port, insecure)
        days_left = (not_after - datetime.now(timezone.utc)).days
        perfdata = {"days_left": days_left, "not_after": not_after.isoformat(), "insecure": insecure}

        if days_left <= crit_days:
            status = CheckStatus.CRITICAL
        elif days_left <= warn_days:
            status = CheckStatus.WARNING
        else:
            status = CheckStatus.OK

        suffix = " (cert. auto-signé, non vérifié)" if insecure else ""
        return CheckResultData(
            status=status,
            value=float(days_left),
            message=f"Certificate expires in {days_left} days{suffix}",
            perfdata=perfdata,
        )

    def _read_not_after(self, ctx: CheckContext, port: int, insecure: bool) -> datetime:
        if insecure:
            # Récupère le certificat sans valider la chaîne de confiance.
            from cryptography import x509

            pem = ssl.get_server_certificate((ctx.hostname_or_ip, port), timeout=ctx.timeout_seconds)
            cert = x509.load_pem_x509_certificate(pem.encode())
            na = cert.not_valid_after_utc  # tz-aware (cryptography ≥ 42)
            return na if na.tzinfo else na.replace(tzinfo=timezone.utc)

        context = ssl.create_default_context()
        with socket.create_connection((ctx.hostname_or_ip, port), timeout=ctx.timeout_seconds) as sock:
            with context.wrap_socket(sock, server_hostname=ctx.hostname_or_ip) as ssock:
                cert = ssock.getpeercert()
        return datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
