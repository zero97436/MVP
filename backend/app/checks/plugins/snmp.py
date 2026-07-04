"""Check snmp : interroge un équipement via SNMP (snmpget de net-snmp).

Idéal pour MikroTik, switches, onduleurs, NAS, imprimantes… qui ne peuvent pas
exécuter l'agent. Active SNMP sur l'équipement (communauté en lecture).

config_json :
  - oid        : OID à interroger (sinon utiliser 'metric' ci-dessous)
  - metric     : raccourci OID courant : 'uptime' | 'cpu' | 'sysdescr' | 'sysname'
  - community  : communauté SNMP (défaut 'public')
  - version    : '1' | '2c' (défaut '2c')

Seuils (warning_threshold / critical_threshold) appliqués si la valeur est
numérique (valeur haute = mauvaise, ex. CPU%). Sinon, statut OK + valeur affichée.
"""
import re
import subprocess

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus

# Raccourcis d'OID standards (MIB-II / HOST-RESOURCES) — compatibles MikroTik.
METRIC_OIDS = {
    "uptime": "1.3.6.1.2.1.1.3.0",            # sysUpTime
    "sysdescr": "1.3.6.1.2.1.1.1.0",          # description
    "sysname": "1.3.6.1.2.1.1.5.0",           # nom
    "cpu": "1.3.6.1.2.1.25.3.3.1.2.1",        # hrProcessorLoad (1er cœur)
}


class SnmpCheck(BaseCheck):
    type = "snmp"

    def run(self, ctx: CheckContext) -> CheckResultData:
        cfg = ctx.config
        community = str(cfg.get("community", "public"))
        version = str(cfg.get("version", "2c"))
        oid = cfg.get("oid") or METRIC_OIDS.get(cfg.get("metric", ""))
        if not oid:
            return CheckResultData(
                status=CheckStatus.UNKNOWN,
                message="Préciser 'oid' ou 'metric' (uptime/cpu/sysdescr/sysname)",
            )

        cmd = [
            "snmpget", "-v", version, "-c", community,
            "-Oqv", "-t", str(max(1, ctx.timeout_seconds)), "-r", "1",
            ctx.hostname_or_ip, oid,
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=ctx.timeout_seconds * 2 + 5)
        except FileNotFoundError:
            return CheckResultData(status=CheckStatus.UNKNOWN, message="snmpget non installé")
        except subprocess.TimeoutExpired:
            return CheckResultData(status=CheckStatus.CRITICAL, message="SNMP : pas de réponse (timeout)")

        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip().splitlines()
            return CheckResultData(
                status=CheckStatus.CRITICAL,
                message=f"SNMP erreur : {err[-1] if err else 'échec'}",
            )

        raw = proc.stdout.strip().strip('"')
        # Tente d'extraire une valeur numérique (CPU%, compteur…).
        num = re.search(r"-?\d+(?:\.\d+)?", raw)
        if num:
            value = float(num.group())
            warn, crit = ctx.warning_threshold, ctx.critical_threshold
            if crit is not None and value >= crit:
                status = CheckStatus.CRITICAL
            elif warn is not None and value >= warn:
                status = CheckStatus.WARNING
            else:
                status = CheckStatus.OK
            return CheckResultData(
                status=status, value=value, message=f"SNMP {oid} = {raw}",
                perfdata={"oid": oid, "value": value},
            )

        return CheckResultData(
            status=CheckStatus.OK, message=f"SNMP {oid} = {raw}", perfdata={"oid": oid}
        )
