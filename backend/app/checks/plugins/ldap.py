"""Check ldap : vérifie la disponibilité d'un service LDAP (connexion TCP).

LDAP est un protocole binaire (pas de bannière texte) : on valide l'ouverture du
port (389 par défaut, 636 pour LDAPS). Pour un test de bind complet, utiliser un
script via `ssh_command` ou étendre avec la lib ldap3.
"""
import socket
import time

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus


class LdapCheck(BaseCheck):
    type = "ldap"

    def run(self, ctx: CheckContext) -> CheckResultData:
        port = int(ctx.config.get("port", 389))
        t0 = time.time()
        try:
            with socket.create_connection((ctx.hostname_or_ip, port), timeout=ctx.timeout_seconds):
                ms = int((time.time() - t0) * 1000)
        except OSError as exc:
            return CheckResultData(status=CheckStatus.CRITICAL, message=f"LDAP injoignable (port {port}): {exc}")
        return CheckResultData(
            status=CheckStatus.OK, value=float(ms),
            message=f"LDAP joignable (port {port}, {ms} ms)",
            perfdata={"response_ms": ms, "port": port},
        )
