"""Check `vmware` : état d'un vCenter/ESXi via l'API REST vSphere (6.5+).

config_json :
  - api_url    : https://vcenter.local
  - user       : compte en LECTURE SEULE recommandé
  - password   : mot de passe (chiffré au repos)
  - verify_ssl : true/false (défaut false — certificat interne)
  - mode       : "hosts" (défaut) | "vms" | "vm"
  - name       : nom de la VM (mode vm)

Statuts :
  - hosts : CRITICAL si un ESXi est déconnecté ou éteint
  - vms   : synthèse allumées/éteintes (informatif, toujours OK si API répond)
  - vm    : CRITICAL si la VM nommée est éteinte/suspendue ou introuvable
"""
import httpx

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus


def _session(api: str, user: str, password: str, verify: bool, timeout: int) -> str:
    """Ouvre une session vSphere ; renvoie le token. Mockable en test."""
    r = httpx.post(f"{api}/rest/com/vmware/cis/session",
                   auth=(user, password), verify=verify, timeout=timeout)
    r.raise_for_status()
    return r.json()["value"]


def _get(api: str, path: str, sid: str, verify: bool, timeout: int):
    """GET authentifié ; renvoie le champ 'value'. Mockable en test."""
    r = httpx.get(f"{api}{path}", headers={"vmware-api-session-id": sid},
                  verify=verify, timeout=timeout)
    r.raise_for_status()
    return r.json().get("value")


class VmwareCheck(BaseCheck):
    type = "vmware"

    def run(self, ctx: CheckContext) -> CheckResultData:
        api = (ctx.config.get("api_url") or "").rstrip("/")
        user = ctx.config.get("user", "")
        password = ctx.config.get("password", "")
        if not api or not user:
            return CheckResultData(status=CheckStatus.UNKNOWN, message="config api_url + user + password requis")
        verify = bool(ctx.config.get("verify_ssl", False))
        mode = ctx.config.get("mode", "hosts")

        try:
            sid = _session(api, user, password, verify, ctx.timeout_seconds)
            if mode == "hosts":
                return self._hosts(_get(api, "/rest/vcenter/host", sid, verify, ctx.timeout_seconds) or [])
            if mode in ("vms", "vm"):
                vms = _get(api, "/rest/vcenter/vm", sid, verify, ctx.timeout_seconds) or []
                if mode == "vms":
                    return self._vms(vms)
                name = ctx.config.get("name", "")
                if not name:
                    return CheckResultData(status=CheckStatus.UNKNOWN, message="config 'name' requise (mode vm)")
                return self._vm(vms, name)
            return CheckResultData(status=CheckStatus.UNKNOWN, message=f"mode inconnu : {mode}")
        except httpx.HTTPStatusError as exc:
            return CheckResultData(
                status=CheckStatus.CRITICAL,
                message=f"API vSphere : HTTP {exc.response.status_code}"
                        + (" (identifiants ?)" if exc.response.status_code in (401, 403) else ""),
            )
        except Exception as exc:  # noqa: BLE001
            return CheckResultData(status=CheckStatus.CRITICAL, message=f"vCenter injoignable : {str(exc)[:100]}")

    def _hosts(self, hosts: list[dict]) -> CheckResultData:
        bad = [h["name"] for h in hosts
               if h.get("connection_state") != "CONNECTED" or h.get("power_state") != "POWERED_ON"]
        perf = {"esxi": len(hosts), "down": len(bad)}
        if bad:
            return CheckResultData(
                status=CheckStatus.CRITICAL, perfdata=perf,
                message=f"{len(bad)} ESXi en anomalie : {', '.join(bad[:5])} ({len(hosts) - len(bad)}/{len(hosts)} OK)",
            )
        return CheckResultData(
            status=CheckStatus.OK, value=float(len(hosts)), perfdata=perf,
            message=f"{len(hosts)} hôte(s) ESXi connecté(s) et allumé(s)",
        )

    def _vms(self, vms: list[dict]) -> CheckResultData:
        on = sum(1 for v in vms if v.get("power_state") == "POWERED_ON")
        return CheckResultData(
            status=CheckStatus.OK, value=float(on),
            perfdata={"vms": len(vms), "powered_on": on},
            message=f"{on}/{len(vms)} VM allumée(s)",
        )

    def _vm(self, vms: list[dict], name: str) -> CheckResultData:
        vm = next((v for v in vms if v.get("name") == name), None)
        if vm is None:
            return CheckResultData(status=CheckStatus.CRITICAL, message=f"VM '{name}' introuvable")
        state = vm.get("power_state", "?")
        if state != "POWERED_ON":
            return CheckResultData(
                status=CheckStatus.CRITICAL, perfdata={"power_state": state},
                message=f"{name} : {state}",
            )
        return CheckResultData(
            status=CheckStatus.OK, perfdata={"power_state": state},
            message=f"{name} : allumée (cpu {vm.get('cpu_count', '?')}, ram {vm.get('memory_size_MiB', '?')} MiB)",
        )
