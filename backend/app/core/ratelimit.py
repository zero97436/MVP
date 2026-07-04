"""Limiteur anti-bruteforce simple, en mémoire (fenêtre glissante par clé).

Suffisant pour un MVP / petit déploiement. Pour du multi-process ou multi-instance,
remplacer par un backend partagé (Redis).
"""
import threading
import time


class RateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window = window_seconds
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> list[float]:
        recent = [t for t in self._hits.get(key, []) if now - t < self.window]
        if recent:
            self._hits[key] = recent
        else:
            self._hits.pop(key, None)
        return recent

    def is_blocked(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            return len(self._prune(key, now)) >= self.max_attempts

    def record_failure(self, key: str) -> None:
        now = time.time()
        with self._lock:
            self._prune(key, now)
            self._hits.setdefault(key, []).append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)


class RedisRateLimiter:
    """Limiteur partagé via Redis (fenêtre fixe par clé). Repli en mémoire si Redis
    est indisponible — l'anti-bruteforce reste actif même en cas de panne Redis."""

    def __init__(self, url: str, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window = window_seconds
        self._fallback = RateLimiter(max_attempts, window_seconds)
        try:
            import redis

            self.r = redis.from_url(url, socket_connect_timeout=1, socket_timeout=1)
        except Exception:  # noqa: BLE001
            self.r = None

    @staticmethod
    def _key(key: str) -> str:
        return f"ratelimit:login:{key}"

    def is_blocked(self, key: str) -> bool:
        if self.r is None:
            return self._fallback.is_blocked(key)
        try:
            return int(self.r.get(self._key(key)) or 0) >= self.max_attempts
        except Exception:  # noqa: BLE001
            return self._fallback.is_blocked(key)

    def record_failure(self, key: str) -> None:
        if self.r is None:
            return self._fallback.record_failure(key)
        try:
            pipe = self.r.pipeline()
            pipe.incr(self._key(key))
            pipe.expire(self._key(key), self.window)
            pipe.execute()
        except Exception:  # noqa: BLE001
            self._fallback.record_failure(key)

    def reset(self, key: str) -> None:
        if self.r is None:
            return self._fallback.reset(key)
        try:
            self.r.delete(self._key(key))
        except Exception:  # noqa: BLE001
            self._fallback.reset(key)


# Limiteur partagé pour le login (Redis, repli mémoire).
from app.core.config import settings  # noqa: E402

login_limiter = RedisRateLimiter(
    settings.REDIS_URL, settings.LOGIN_MAX_ATTEMPTS, settings.LOGIN_WINDOW_SECONDS
)
