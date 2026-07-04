from app.core.ratelimit import RateLimiter, RedisRateLimiter, login_limiter


def test_rate_limiter_blocks_after_max():
    rl = RateLimiter(max_attempts=3, window_seconds=60)
    assert not rl.is_blocked("ip")
    for _ in range(3):
        rl.record_failure("ip")
    assert rl.is_blocked("ip")
    rl.reset("ip")
    assert not rl.is_blocked("ip")


def test_login_blocks_bruteforce(client):
    # On nettoie l'état partagé avant/après pour ne pas gêner les autres tests.
    login_limiter.reset("testclient")
    try:
        # Dépasse la limite avec de mauvais identifiants.
        last = None
        for _ in range(login_limiter.max_attempts + 1):
            last = client.post("/api/auth/login", json={"email": "admin@local", "password": "wrong"})
        assert last.status_code == 429
    finally:
        login_limiter.reset("testclient")


def test_login_still_works_after_reset(client):
    login_limiter.reset("testclient")
    resp = client.post("/api/auth/login", json={"email": "admin@local", "password": "admin1234"})
    assert resp.status_code == 200


def test_redis_limiter_falls_back_when_unreachable():
    # URL Redis injoignable -> repli mémoire, l'anti-bruteforce reste fonctionnel.
    rl = RedisRateLimiter("redis://127.0.0.1:1", max_attempts=2, window_seconds=60)
    rl.reset("k")
    assert not rl.is_blocked("k")
    rl.record_failure("k")
    rl.record_failure("k")
    assert rl.is_blocked("k")
    rl.reset("k")
    assert not rl.is_blocked("k")
