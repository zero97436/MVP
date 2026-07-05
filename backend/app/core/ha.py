"""Haute disponibilité : élection de leader du scheduler via verrou Redis.

Problème : si l'on exécute plusieurs conteneurs `scheduler` (pour la tolérance
aux pannes), ils déclencheraient TOUS les checks -> exécutions dupliquées.

Solution : un seul scheduler est « leader » à la fois. Le leader détient un
verrou Redis avec TTL qu'il renouvelle à chaque tick. S'il meurt, le verrou
expire et un scheduler en attente le récupère -> bascule automatique en
quelques secondes, sans intervention.

Toujours actif (même avec un seul scheduler) : c'est une garantie de correction,
pas seulement une option — négligeable en coût, évite tout doublon d'exécution.
Le repli mémoire (Redis indisponible) considère l'instance comme leader : en
mono-instance, le scheduler continue de fonctionner même si Redis est down.
"""
from __future__ import annotations

import os
import socket
import time

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("ha")

LOCK_KEY = "opsora:scheduler:leader"
# Le verrou expire après ~3 ticks manqués : bascule rapide mais sans « flapping ».
LOCK_TTL_SECONDS = max(15, settings.SCHEDULER_INTERVAL_SECONDS * 3)

# Renouvelle le verrou uniquement si on le détient déjà (compare-and-set atomique).
_RENEW_LUA = """
if redis.call('get', KEYS[1]) == ARGV[1] then
  return redis.call('pexpire', KEYS[1], ARGV[2])
else
  return 0
end
"""


class LeaderElector:
    def __init__(self, redis_url: str | None = None):
        self.node_id = f"{socket.gethostname()}:{os.getpid()}"
        self._is_leader = False
        self._r = None
        try:
            import redis

            self._r = redis.from_url(
                redis_url or settings.REDIS_URL,
                socket_connect_timeout=1, socket_timeout=1, decode_responses=True,
            )
            self._r.ping()
            logger.info("HA : élection de leader via Redis (node=%s)", self.node_id)
        except Exception as exc:  # noqa: BLE001
            self._r = None
            logger.warning("HA : Redis indisponible (%s) -> mode mono-instance (leader local)", exc)

    def is_leader(self) -> bool:
        return self._is_leader

    def try_acquire_or_renew(self) -> bool:
        """À appeler à chaque tick. Renvoie True si cette instance est leader."""
        if self._r is None:
            self._is_leader = True  # pas de Redis -> mono-instance, on est leader
            return True
        ttl_ms = LOCK_TTL_SECONDS * 1000
        try:
            if self._is_leader:
                # Renouvelle notre bail (seulement si on le détient toujours).
                held = self._r.eval(_RENEW_LUA, 1, LOCK_KEY, self.node_id, ttl_ms)
                if not held:
                    self._is_leader = False  # on a perdu le leadership
            if not self._is_leader:
                # Tente de prendre le verrou (SET NX) — succès = on devient leader.
                if self._r.set(LOCK_KEY, self.node_id, nx=True, px=ttl_ms):
                    self._is_leader = True
                    logger.info("HA : cette instance devient LEADER (node=%s)", self.node_id)
        except Exception as exc:  # noqa: BLE001
            # Panne Redis transitoire : on ne bascule pas brutalement, on garde
            # l'état courant (évite un split-brain dû à un simple hoquet réseau).
            logger.warning("HA : erreur Redis pendant l'élection : %s", exc)
        return self._is_leader

    def release(self) -> None:
        """Libère le verrou proprement à l'arrêt (bascule immédiate)."""
        if self._r is not None and self._is_leader:
            try:
                if self._r.get(LOCK_KEY) == self.node_id:
                    self._r.delete(LOCK_KEY)
            except Exception:  # noqa: BLE001
                pass
        self._is_leader = False

    def status(self) -> dict:
        """État du cluster (pour l'endpoint HA)."""
        info = {
            "node_id": self.node_id,
            "is_leader": self._is_leader,
            "redis": self._r is not None,
            "current_leader": None,
            "lock_ttl_seconds": LOCK_TTL_SECONDS,
        }
        if self._r is not None:
            try:
                info["current_leader"] = self._r.get(LOCK_KEY)
            except Exception:  # noqa: BLE001
                info["redis"] = False
        return info


def read_leader() -> dict:
    """Lecture seule de l'état du leader (pour l'API, hors scheduler)."""
    out = {"redis": False, "current_leader": None, "last_heartbeat_age": None}
    try:
        import redis

        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1,
                           socket_timeout=1, decode_responses=True)
        out["current_leader"] = r.get(LOCK_KEY)
        ttl = r.pttl(LOCK_KEY)  # ms restant avant expiration du bail
        if ttl and ttl > 0:
            out["last_heartbeat_age"] = round((LOCK_TTL_SECONDS * 1000 - ttl) / 1000, 1)
        out["redis"] = True
    except Exception:  # noqa: BLE001
        pass
    return out
