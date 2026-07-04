"""Découverte réseau : scanne une plage d'IP (ping + ports courants) et propose
les équipements trouvés à importer en supervision.
"""
from __future__ import annotations

import ipaddress
import platform
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.host import Host

# Ports courants -> type de check suggéré (sinon tcp_port générique).
PORT_CHECK = {22: "ssh", 80: "http", 25: "smtp", 21: "ftp"}
COMMON_PORTS = [22, 80, 443, 3389, 8080, 8443, 21, 25, 3306, 5432]
MAX_HOSTS = 256


def _ping(ip: str, timeout: int = 1) -> bool:
    win = platform.system().lower() == "windows"
    cmd = ["ping", "-n" if win else "-c", "1", "-w" if win else "-W",
           str(timeout * 1000 if win else timeout), ip]
    try:
        return subprocess.run(cmd, capture_output=True, timeout=timeout + 2).returncode == 0
    except Exception:  # noqa: BLE001
        return False


def _scan_port(ip: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((ip, port)) == 0
    except OSError:
        return False


class DiscoveryService:
    def __init__(self, db: Session):
        self.db = db

    def scan(self, target: str, ports: list[int] | None = None) -> list[dict]:
        ports = ports or COMMON_PORTS
        ips = self._expand(target)
        known = {h.hostname_or_ip for h in self.db.scalars(select(Host))}

        def probe(ip: str) -> dict | None:
            open_ports = [p for p in ports if _scan_port(ip, p)]
            alive = bool(open_ports) or _ping(ip)
            if not alive:
                return None
            return {
                "ip": ip,
                "open_ports": open_ports,
                "already_monitored": ip in known,
                "suggested_checks": self._suggest(ip, open_ports),
            }

        with ThreadPoolExecutor(max_workers=64) as pool:
            results = [r for r in pool.map(probe, ips) if r]
        results.sort(key=lambda r: tuple(int(o) for o in r["ip"].split(".")))
        return results

    def _expand(self, target: str) -> list[str]:
        target = target.strip()
        try:
            net = ipaddress.ip_network(target, strict=False)
        except ValueError:
            # IP unique ou nom -> on tente tel quel.
            return [target]
        hosts = [str(ip) for ip in net.hosts()] or [str(net.network_address)]
        if len(hosts) > MAX_HOSTS:
            raise ValueError(f"Plage trop grande ({len(hosts)} > {MAX_HOSTS}). Limitez à un /24.")
        return hosts

    def _suggest(self, ip: str, open_ports: list[int]) -> list[dict]:
        checks: list[dict] = [{"name": "Ping", "type": "ping", "config_json": {}}]
        for p in open_ports:
            ctype = PORT_CHECK.get(p, "tcp_port")
            if ctype == "http":
                checks.append({"name": "HTTP", "type": "http", "config_json": {"url": f"http://{ip}"}})
            elif ctype == "tcp_port":
                checks.append({"name": f"Port {p}", "type": "tcp_port", "config_json": {"port": p}})
            else:
                checks.append({"name": ctype.upper(), "type": ctype, "config_json": {"port": p}})
        return checks
