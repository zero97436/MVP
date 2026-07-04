#!/usr/bin/env python3
"""Agent de collecte minimal pour supervision-house.

Pousse périodiquement CPU / RAM / disque / réseau de la machine locale vers
l'endpoint d'ingestion. À installer sur chaque hôte à superviser.

Dépendances : pip install psutil requests

Exemple :
    python agent_example.py \
        --url http://localhost:8000/api/metrics/ingest \
        --host-id 1 \
        --key "$INGEST_API_KEY" \
        --interval 30
"""
import argparse
import socket
import subprocess
import time
from datetime import datetime, timezone

import psutil
import requests

_last_net = None


def net_mbps(interval: float) -> float:
    """Débit réseau total (in+out) en Mbit/s sur l'intervalle."""
    global _last_net
    counters = psutil.net_io_counters()
    total = counters.bytes_sent + counters.bytes_recv
    if _last_net is None:
        _last_net = total
        return 0.0
    delta_bytes = total - _last_net
    _last_net = total
    return round((delta_bytes * 8) / 1_000_000 / max(interval, 1), 1)


def collect_disks() -> dict[str, float]:
    """Pourcentage d'utilisation par partition (lecture seule, ignore les CD/erreurs)."""
    disks: dict[str, float] = {}
    for part in psutil.disk_partitions(all=False):
        if "cdrom" in part.opts or part.fstype == "":
            continue
        try:
            disks[part.device.rstrip("\\/")] = psutil.disk_usage(part.mountpoint).percent
        except (PermissionError, OSError):
            continue
    return disks


# --- Remédiation Niveau 2 : liste blanche LOCALE de l'agent ---------------- #
# L'agent n'exécute QUE les actions ci-dessous. Toute autre action demandée par
# le backend est refusée. Par défaut, uniquement des actions de DIAGNOSTIC
# (lecture seule) — sûres sur une machine réelle.

def _cmd_top_processes() -> str:
    procs = []
    for p in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
        procs.append(p.info)
    procs.sort(key=lambda x: (x.get("cpu_percent") or 0), reverse=True)
    lines = ["Top processus (CPU%) :"]
    for p in procs[:8]:
        lines.append(
            f"  {p.get('name','?'):<28} CPU {p.get('cpu_percent',0):5.1f}%  "
            f"RAM {p.get('memory_percent',0):4.1f}%"
        )
    return "\n".join(lines)


def _cmd_collect_now() -> str:
    return "Échantillon de métriques transmis."


COMMAND_HANDLERS = {
    "top_processes": _cmd_top_processes,
    "collect_now": _cmd_collect_now,
}


def poll_and_run_commands(api_base: str, host_id, hostname, headers: dict) -> None:
    params = {"host_id": host_id} if host_id else {"hostname_or_ip": hostname}
    try:
        r = requests.get(f"{api_base}/agent/commands", params=params, headers=headers, timeout=10)
        if r.status_code != 200:
            return
        commands = r.json()
    except requests.RequestException:
        return
    for cmd in commands:
        action = cmd.get("action")
        handler = COMMAND_HANDLERS.get(action)
        if handler is None:
            status, result = "failed", f"Action '{action}' non autorisée par l'agent."
        else:
            try:
                result = handler()
                status = "done"
            except Exception as exc:  # noqa: BLE001
                status, result = "failed", f"Erreur: {exc}"
        try:
            requests.post(
                f"{api_base}/agent/commands/{cmd['id']}/result",
                json={"status": status, "result": result},
                headers=headers,
                timeout=10,
            )
            print(f"  commande #{cmd['id']} ({action}) -> {status}")
        except requests.RequestException:
            pass


# --- Agent-sonde : exécution de checks contre d'autres équipements ---------- #
# L'agent exécute les checks que le serveur lui a assignés (executor_host_id),
# contre des cibles de SON réseau, puis pousse les résultats.

def _run_ping(target: str, cfg: dict, timeout: int) -> dict:
    import platform as _pf
    count = str(cfg.get("count", 2))
    win = _pf.system().lower() == "windows"
    cmd = ["ping", "-n" if win else "-c", count,
           "-w" if win else "-W", str(timeout * 1000 if win else timeout), target]
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    ms = round((time.time() - t0) * 1000)
    if proc.returncode == 0:
        return {"status": "OK", "message": f"{target} reachable", "duration_ms": ms, "perfdata": {"returncode": 0}}
    return {"status": "CRITICAL", "message": f"{target} unreachable", "duration_ms": ms, "perfdata": {"returncode": proc.returncode}}


def _run_tcp(target: str, cfg: dict, timeout: int) -> dict:
    import socket
    port = int(cfg.get("port", 0))
    t0 = time.time()
    try:
        with socket.create_connection((target, port), timeout=timeout):
            ms = round((time.time() - t0) * 1000)
            return {"status": "OK", "message": f"Port {port} open ({ms} ms)", "duration_ms": ms, "perfdata": {"connect_ms": ms, "port": port}}
    except OSError as exc:
        return {"status": "CRITICAL", "message": f"Port {port} fermé ({exc})", "duration_ms": None, "perfdata": {"port": port}}


def _run_http(target: str, cfg: dict, timeout: int, warn, crit) -> dict:
    url = cfg.get("url") or f"http://{target}"
    expected = int(cfg.get("expected_status", 200))
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True)
        ms = round(r.elapsed.total_seconds() * 1000)
        perf = {"status_code": r.status_code, "response_ms": ms}
        if r.status_code != expected:
            return {"status": "CRITICAL", "value": ms, "message": f"HTTP {r.status_code} (attendu {expected})", "duration_ms": ms, "perfdata": perf}
        status = "OK"
        if crit is not None and ms >= crit:
            status = "CRITICAL"
        elif warn is not None and ms >= warn:
            status = "WARNING"
        return {"status": status, "value": ms, "message": f"HTTP {r.status_code} en {ms} ms", "duration_ms": ms, "perfdata": perf}
    except requests.RequestException as exc:
        return {"status": "CRITICAL", "message": f"Échec HTTP : {exc}", "duration_ms": None, "perfdata": {}}


def _run_windows_service(target: str, cfg: dict, timeout: int) -> dict:
    name = cfg.get("service")
    if not name:
        return {"status": "UNKNOWN", "message": "config 'service' manquante"}
    try:
        svc = psutil.win_service_get(name)
        st = svc.status()
        return {
            "status": "OK" if st == "running" else "CRITICAL",
            "message": f"Service '{name}' : {st}",
            "perfdata": {"state": st},
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "CRITICAL", "message": f"Service '{name}' introuvable/erreur : {exc}"}


CHECK_RUNNERS = {
    "ping": _run_ping, "tcp_port": _run_tcp, "http": _run_http,
    "windows_service": _run_windows_service,
}


def poll_and_run_checks(api_base: str, host_id, hostname, headers: dict) -> None:
    params = {"host_id": host_id} if host_id else {"hostname_or_ip": hostname}
    try:
        r = requests.get(f"{api_base}/agent/checks", params=params, headers=headers, timeout=10)
        if r.status_code != 200:
            return
        checks = r.json()
    except requests.RequestException:
        return
    for c in checks:
        runner = CHECK_RUNNERS.get(c["type"])
        cfg = c.get("config") or {}
        if runner is None:
            result = {"status": "UNKNOWN", "message": f"Type '{c['type']}' non supporté par l'agent-sonde"}
        elif c["type"] == "http":
            result = runner(c["target"], cfg, c["timeout_seconds"], c.get("warning_threshold"), c.get("critical_threshold"))
        else:
            result = runner(c["target"], cfg, c["timeout_seconds"])
        try:
            requests.post(f"{api_base}/agent/checks/{c['id']}/result", json=result, headers=headers, timeout=10)
            print(f"  check #{c['id']} ({c['type']} -> {c['target']}) : {result['status']}")
        except requests.RequestException:
            pass


def _load1() -> float | None:
    try:
        return round(psutil.getloadavg()[0], 2)
    except (AttributeError, OSError):
        return None


def _temperature() -> float | None:
    try:
        temps = psutil.sensors_temperatures()  # absent sur Windows -> {}
    except AttributeError:
        return None
    vals = [s.current for entries in (temps or {}).values() for s in entries if s.current]
    return round(max(vals), 1) if vals else None


def sample(interval: float) -> dict:
    disks = collect_disks()
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "mem_percent": psutil.virtual_memory().percent,
        # disk_percent = disque le plus rempli (pour la courbe de tendance).
        "disk_percent": max(disks.values()) if disks else None,
        "disks": disks,
        "net_mbps": net_mbps(interval),
        "process_count": len(psutil.pids()),
        "load1": _load1(),
        "temperature": _temperature(),
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="supervision-house metric agent")
    p.add_argument("--url", required=True, help="URL de l'endpoint /api/metrics/ingest")
    p.add_argument("--host-id", type=int, help="ID de l'hôte côté supervision-house")
    p.add_argument("--hostname", help="hostname_or_ip de l'hôte (alternative à --host-id)")
    p.add_argument("--key", default="", help="Clé X-Ingest-Key")
    p.add_argument("--interval", type=float, default=30.0, help="Période en secondes")
    p.add_argument("--once", action="store_true", help="Envoie un seul échantillon puis quitte")
    args = p.parse_args()

    if not args.host_id and not args.hostname:
        p.error("Fournir --host-id OU --hostname")

    headers = {"X-Ingest-Key": args.key} if args.key else {}
    # Base API déduite de l'URL d'ingestion (…/api/metrics/ingest -> …/api).
    api_base = args.url.rsplit("/metrics/ingest", 1)[0]
    psutil.cpu_percent(interval=None)  # amorce la mesure CPU

    while True:
        payload = sample(args.interval)
        if args.host_id:
            payload["host_id"] = args.host_id
        else:
            payload["hostname_or_ip"] = args.hostname
        try:
            r = requests.post(args.url, json=payload, headers=headers, timeout=10)
            print(f"{payload['collected_at']} -> {r.status_code}")
        except requests.RequestException as exc:
            print(f"Erreur d'envoi : {exc}")
        # Récupère et exécute les éventuelles commandes de remédiation (liste blanche).
        poll_and_run_commands(api_base, args.host_id, args.hostname, headers)
        # Exécute les checks assignés à cet agent-sonde (poller) contre d'autres cibles.
        poll_and_run_checks(api_base, args.host_id, args.hostname, headers)
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
