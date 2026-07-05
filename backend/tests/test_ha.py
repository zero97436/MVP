"""HA : élection de leader du scheduler (verrou Redis) + gating de l'endpoint."""
import app.core.license as lic
from app.core.ha import LeaderElector


class FakeRedis:
    """Redis en mémoire minimal : SET NX/PX, GET, eval(renew), delete, pttl."""
    def __init__(self):
        self.store: dict[str, str] = {}

    def ping(self):
        return True

    def set(self, key, val, nx=False, px=None):
        if nx and key in self.store:
            return None
        self.store[key] = val
        return True

    def get(self, key):
        return self.store.get(key)

    def delete(self, key):
        self.store.pop(key, None)

    def pttl(self, key):
        return 30000 if key in self.store else -2

    def eval(self, script, numkeys, key, val, ttl):
        # Renouvelle uniquement si le détenteur correspond (compare-and-set).
        return 1 if self.store.get(key) == val else 0


def _elector(shared: FakeRedis, node: str) -> LeaderElector:
    e = LeaderElector.__new__(LeaderElector)
    e.node_id = node
    e._is_leader = False
    e._r = shared
    return e


def test_single_leader_among_two_schedulers():
    redis = FakeRedis()
    a = _elector(redis, "sched-a")
    b = _elector(redis, "sched-b")

    # a prend le verrou en premier -> leader ; b reste en attente.
    assert a.try_acquire_or_renew() is True
    assert b.try_acquire_or_renew() is False
    assert a.is_leader() and not b.is_leader()

    # a renouvelle son bail à chaque tick ; b ne peut pas le voler.
    assert a.try_acquire_or_renew() is True
    assert b.try_acquire_or_renew() is False


def test_failover_when_leader_dies():
    redis = FakeRedis()
    a = _elector(redis, "sched-a")
    b = _elector(redis, "sched-b")
    a.try_acquire_or_renew()             # a = leader
    b.try_acquire_or_renew()             # b = attente

    # a « meurt » : son bail expire (on simule l'expiration du verrou Redis).
    redis.store.clear()

    # b devient leader au tick suivant -> bascule automatique.
    assert b.try_acquire_or_renew() is True
    assert b.is_leader()


def test_release_frees_lock_for_immediate_failover():
    redis = FakeRedis()
    a = _elector(redis, "sched-a")
    b = _elector(redis, "sched-b")
    a.try_acquire_or_renew()
    a.release()                          # arrêt propre de a
    assert b.try_acquire_or_renew() is True  # b prend le relais tout de suite


def test_no_redis_means_local_leader():
    """Sans Redis (mono-instance), le scheduler reste leader et fonctionne."""
    e = LeaderElector.__new__(LeaderElector)
    e.node_id = "solo"
    e._is_leader = False
    e._r = None
    assert e.try_acquire_or_renew() is True


def test_ha_status_requires_enterprise(client, monkeypatch):
    monkeypatch.setattr(lic, "get_license", lambda: {
        "plan": "business", "max_hosts": None,
        "features": sorted(lic.PLAN_FEATURES["business"]), "customer": None, "expires": None,
    })
    assert client.get("/api/ha/status").status_code == 403  # ha = Enterprise


def test_ha_status_enterprise(client):
    r = client.get("/api/ha/status")  # licence Enterprise par défaut en test
    assert r.status_code == 200
    body = r.json()
    assert "scheduler_leader" in body and "healthy" in body
