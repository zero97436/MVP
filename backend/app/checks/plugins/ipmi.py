"""Check `ipmi` : santé matérielle d'un serveur via Redfish (iDRAC, iLO, BMC…).

Redfish est l'API REST standard des cartes de gestion modernes (DMTF) —
successeur d'IPMI, supporté par Dell iDRAC 7+, HPE iLO 4+, Lenovo XCC, Supermicro…

config_json :
  - api_url     : https://idrac.local (la carte de gestion, pas l'OS)
  - user        : compte en LECTURE SEULE recommandé
  - password    : mot de passe (chiffré au repos)
  - verify_ssl  : true/false (défaut false — certificat embarqué)
  - check_power : alerter si le serveur est éteint (défaut true)

Statuts : CRITICAL si santé Critical ou serveur éteint · WARNING si santé Warning.
"""
import httpx

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus


def _get(url: str, user: str, password: str, verify: bool, timeout: int) -> dict:
    """GET Redfish en basic auth. Mockable en test."""
    r = httpx.get(url, auth=(user, password), verify=verify, timeout=timeout)
    r.raise_for_status()
    return r.json()


class IpmiCheck(BaseCheck):
    type = "ipmi"

    def run(self, ctx: CheckContext) -> CheckResultData:
        api = (ctx.config.get("api_url") or "").rstrip("/")
        user = ctx.config.get("user", "")
        password = ctx.config.get("password", "")
        if not api or not user:
            return CheckResultData(status=CheckStatus.UNKNOWN, message="config api_url + user + password requis")
        verify = bool(ctx.config.get("verify_ssl", False))
        check_power = bool(ctx.config.get("check_power", True))

        try:
            root = _get(f"{api}/redfish/v1/Systems", user, password, verify, ctx.timeout_seconds)
            members = [m.get("@odata.id") for m in root.get("Members", []) if m.get("@odata.id")]
            if not members:
                return CheckResultData(status=CheckStatus.UNKNOWN, message="Aucun système Redfish exposé")

            systems = []
            for path in members:
                sysinfo = _get(f"{api}{path}", user, password, verify, ctx.timeout_seconds)
                systems.append({
                    "name": sysinfo.get("Model") or sysinfo.get("Id") or path,
                    "health": (sysinfo.get("Status") or {}).get("Health") or "Unknown",
                    "power": sysinfo.get("PowerState", "Unknown"),
                })
        except httpx.HTTPStatusError as exc:
            return CheckResultData(
                status=CheckStatus.CRITICAL,
                message=f"Redfish : HTTP {exc.response.status_code}"
                        + (" (identifiants ?)" if exc.response.status_code in (401, 403) else ""),
            )
        except Exception as exc:  # noqa: BLE001
            return CheckResultData(status=CheckStatus.CRITICAL, message=f"BMC injoignable : {str(exc)[:100]}")

        critical = [s for s in systems if s["health"] == "Critical"
                    or (check_power and s["power"] not in ("On", "Unknown"))]
        warning = [s for s in systems if s["health"] == "Warning"]
        perf = {"systems": [{**s} for s in systems]}

        if critical:
            det = ", ".join(f"{s['name']} (santé {s['health']}, alim {s['power']})" for s in critical[:3])
            return CheckResultData(status=CheckStatus.CRITICAL, perfdata=perf,
                                   message=f"Matériel en défaut : {det}")
        if warning:
            det = ", ".join(s["name"] for s in warning[:3])
            return CheckResultData(status=CheckStatus.WARNING, perfdata=perf,
                                   message=f"Avertissement matériel : {det}")
        names = ", ".join(s["name"] for s in systems[:3])
        return CheckResultData(status=CheckStatus.OK, value=float(len(systems)), perfdata=perf,
                               message=f"Matériel sain : {names} (santé OK, sous tension)")
