"""Check `proxmox` : état d'un hyperviseur Proxmox VE via son API (token).

config_json :
  - api_url      : https://proxmox:8006
  - token_id     : ex. "supervision@pve!monitoring"
  - token_secret : secret du token API (créer un token LECTURE SEULE : rôle PVEAuditor)
  - verify_ssl   : true/false (défaut false — certificat auto-signé)
  - mode         : "cluster" (défaut, tous les nodes) | "vms" (toutes les VM/CT d'un node)
                   | "vm" (une VM précise)
  - node         : nom du node (modes vms/vm)
  - vmid         : id numérique de la VM (mode vm)

Statuts :
  - cluster : CRITICAL si un node offline
  - vms     : CRITICAL si une VM/CT censée tourner est stopped (hors template)
  - vm      : CRITICAL si stopped ; seuils warning/critical du check = CPU % de la VM
"""
import httpx

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus


def _fetch_json(url: str, token_id: str, secret: str, verify: bool, timeout: int) -> dict:
    """Isolé pour être mockable en test."""
    r = httpx.get(
        url,
        headers={"Authorization": f"PVEAPIToken={token_id}={secret}"},
        verify=verify, timeout=timeout,
    )
    r.raise_for_status()
    return r.json()


class ProxmoxCheck(BaseCheck):
    type = "proxmox"

    def run(self, ctx: CheckContext) -> CheckResultData:
        api = (ctx.config.get("api_url") or "").rstrip("/")
        tid = ctx.config.get("token_id", "")
        secret = ctx.config.get("token_secret", "")
        if not api or not tid or not secret:
            return CheckResultData(
                status=CheckStatus.UNKNOWN, message="config api_url + token_id + token_secret requis"
            )
        verify = bool(ctx.config.get("verify_ssl", False))
        mode = ctx.config.get("mode", "cluster")
        node = ctx.config.get("node", "")

        try:
            if mode == "cluster":
                data = _fetch_json(f"{api}/api2/json/nodes", tid, secret, verify, ctx.timeout_seconds)
                return self._cluster(data)
            if mode == "vms":
                if not node:
                    return CheckResultData(status=CheckStatus.UNKNOWN, message="config 'node' requise")
                qemu = _fetch_json(f"{api}/api2/json/nodes/{node}/qemu", tid, secret, verify, ctx.timeout_seconds)
                lxc = _fetch_json(f"{api}/api2/json/nodes/{node}/lxc", tid, secret, verify, ctx.timeout_seconds)
                return self._vms(node, (qemu.get("data") or []) + (lxc.get("data") or []))
            if mode == "vm":
                vmid = ctx.config.get("vmid")
                if not node or not vmid:
                    return CheckResultData(status=CheckStatus.UNKNOWN, message="config 'node' + 'vmid' requises")
                data = _fetch_json(
                    f"{api}/api2/json/nodes/{node}/qemu/{vmid}/status/current",
                    tid, secret, verify, ctx.timeout_seconds,
                )
                return self._vm(ctx, node, data.get("data") or {})
            return CheckResultData(status=CheckStatus.UNKNOWN, message=f"mode inconnu : {mode}")
        except httpx.HTTPStatusError as exc:
            return CheckResultData(
                status=CheckStatus.CRITICAL, message=f"API Proxmox : HTTP {exc.response.status_code}"
            )
        except Exception as exc:  # noqa: BLE001
            return CheckResultData(
                status=CheckStatus.CRITICAL, message=f"API Proxmox injoignable : {str(exc)[:100]}"
            )

    def _cluster(self, data: dict) -> CheckResultData:
        nodes = data.get("data") or []
        offline = [n["node"] for n in nodes if n.get("status") != "online"]
        perf = {"nodes": len(nodes), "offline": len(offline)}
        if offline:
            return CheckResultData(
                status=CheckStatus.CRITICAL, perfdata=perf,
                message=f"{len(offline)} node(s) offline : {', '.join(offline[:5])}",
            )
        return CheckResultData(
            status=CheckStatus.OK, value=float(len(nodes)), perfdata=perf,
            message=f"{len(nodes)} node(s) Proxmox online",
        )

    def _vms(self, node: str, vms: list[dict]) -> CheckResultData:
        real = [v for v in vms if not v.get("template")]
        stopped = [str(v.get("name") or v.get("vmid")) for v in real if v.get("status") == "stopped"]
        running = len(real) - len(stopped)
        perf = {"vms": len(real), "running": running, "stopped": len(stopped)}
        if stopped:
            return CheckResultData(
                status=CheckStatus.CRITICAL, value=float(running), perfdata=perf,
                message=f"[{node}] {len(stopped)} VM/CT stoppée(s) : {', '.join(stopped[:5])} ({running}/{len(real)} up)",
            )
        return CheckResultData(
            status=CheckStatus.OK, value=float(running), perfdata=perf,
            message=f"[{node}] {running}/{len(real)} VM/CT en fonctionnement",
        )

    def _vm(self, ctx: CheckContext, node: str, st: dict) -> CheckResultData:
        name = st.get("name", f"vm{st.get('vmid', '?')}")
        if st.get("status") != "running":
            return CheckResultData(
                status=CheckStatus.CRITICAL,
                message=f"[{node}] {name} : {st.get('status', 'inconnu')}",
                perfdata={"status": st.get("status")},
            )
        cpu = round((st.get("cpu") or 0) * 100, 1)
        mem_pct = round(st.get("mem", 0) / st["maxmem"] * 100, 1) if st.get("maxmem") else None
        perf = {"cpu_percent": cpu, "mem_percent": mem_pct, "uptime": st.get("uptime")}
        warn, crit = ctx.warning_threshold, ctx.critical_threshold
        if crit is not None and cpu >= crit:
            status = CheckStatus.CRITICAL
        elif warn is not None and cpu >= warn:
            status = CheckStatus.WARNING
        else:
            status = CheckStatus.OK
        mem_txt = f", RAM {mem_pct}%" if mem_pct is not None else ""
        return CheckResultData(
            status=status, value=cpu, perfdata=perf,
            message=f"[{node}] {name} : running — CPU {cpu}%{mem_txt}",
        )
