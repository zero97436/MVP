"""Supervision Docker : liste et stats des conteneurs via l'API Docker Engine.

Parle directement au socket unix (monté dans le conteneur : /var/run/docker.sock).
⚠️ Le socket Docker donne un contrôle total sur l'hôte — accès lecture seule ici,
   et l'API n'est exposée qu'aux utilisateurs authentifiés.
"""
from __future__ import annotations

import os

import httpx

from app.core.config import settings


class DockerUnavailable(Exception):
    """Socket Docker absent ou API injoignable."""


def _client() -> httpx.Client:
    sock = settings.DOCKER_SOCKET
    if not os.path.exists(sock):
        raise DockerUnavailable(f"Socket Docker absent ({sock}) — monter /var/run/docker.sock")
    transport = httpx.HTTPTransport(uds=sock)
    return httpx.Client(transport=transport, base_url="http://docker", timeout=10)


def ping() -> bool:
    try:
        with _client() as c:
            return c.get("/_ping").status_code == 200
    except DockerUnavailable:
        return False
    except Exception:  # noqa: BLE001
        return False


def list_containers(with_stats: bool = False) -> list[dict]:
    """Liste tous les conteneurs (running + stopped), stats optionnelles."""
    try:
        with _client() as c:
            raw = c.get("/containers/json", params={"all": "true"}).json()
            out = []
            for ct in raw:
                item = {
                    "id": ct["Id"][:12],
                    "name": (ct.get("Names") or ["?"])[0].lstrip("/"),
                    "image": ct.get("Image", ""),
                    "state": ct.get("State", "unknown"),      # running/exited/restarting…
                    "status": ct.get("Status", ""),           # "Up 3 hours (healthy)"
                    "health": _health_from_status(ct.get("Status", "")),
                    "cpu_percent": None,
                    "mem_percent": None,
                    "mem_usage_mb": None,
                }
                if with_stats and item["state"] == "running":
                    try:
                        item.update(_stats(c, ct["Id"]))
                    except Exception:  # noqa: BLE001 — stats best-effort
                        pass
                out.append(item)
            order = {"exited": 0, "dead": 0, "restarting": 1, "paused": 2, "running": 3}
            out.sort(key=lambda x: (order.get(x["state"], 2), x["name"]))
            return out
    except DockerUnavailable:
        raise
    except Exception as exc:  # noqa: BLE001
        raise DockerUnavailable(f"API Docker injoignable : {str(exc)[:120]}")


def _health_from_status(status: str) -> str | None:
    s = status.lower()
    if "(healthy" in s:
        return "healthy"
    if "(unhealthy" in s:
        return "unhealthy"
    if "health: starting" in s:
        return "starting"
    return None


def _stats(c: httpx.Client, container_id: str) -> dict:
    """Snapshot CPU/mémoire d'un conteneur (une requête, sans stream)."""
    s = c.get(f"/containers/{container_id}/stats", params={"stream": "false"}).json()
    cpu = None
    try:
        cpu_delta = s["cpu_stats"]["cpu_usage"]["total_usage"] - s["precpu_stats"]["cpu_usage"]["total_usage"]
        sys_delta = s["cpu_stats"]["system_cpu_usage"] - s["precpu_stats"].get("system_cpu_usage", 0)
        ncpu = s["cpu_stats"].get("online_cpus") or len(s["cpu_stats"]["cpu_usage"].get("percpu_usage") or [1])
        if sys_delta > 0:
            cpu = round(cpu_delta / sys_delta * ncpu * 100, 1)
    except (KeyError, TypeError, ZeroDivisionError):
        pass
    mem_pct = mem_mb = None
    try:
        usage = s["memory_stats"]["usage"] - s["memory_stats"].get("stats", {}).get("inactive_file", 0)
        limit = s["memory_stats"]["limit"]
        mem_mb = round(usage / 1024 / 1024, 1)
        if limit:
            mem_pct = round(usage / limit * 100, 1)
    except (KeyError, TypeError, ZeroDivisionError):
        pass
    return {"cpu_percent": cpu, "mem_percent": mem_pct, "mem_usage_mb": mem_mb}
