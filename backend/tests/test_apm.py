from app.checks.base import CheckContext
from app.checks.plugins.apm import ApmCheck


def _ingest(client, app="shop", requests=100, errors=0, latency=120.0):
    r = client.post("/api/apm/ingest", json={
        "app_name": app, "requests": requests, "errors": errors, "latency_ms": latency,
    })
    assert r.status_code == 201
    return r


def test_apm_ingest_and_apps(client):
    _ingest(client, app="shop", requests=300, errors=6, latency=150)
    apps = client.get("/api/apm/apps").json()
    shop = next(a for a in apps if a["app_name"] == "shop")
    assert shop["requests"] == 300
    assert shop["errors"] == 6
    assert shop["error_rate"] == 2.0
    assert shop["latency_ms"] == 150.0
    assert shop["rpm"] == 20.0  # 300 req / 15 min


def test_apm_series(client):
    _ingest(client, app="api-facturation", requests=60, errors=3, latency=90)
    series = client.get("/api/apm/apps/api-facturation/series", params={"hours": 1, "buckets": 6}).json()
    assert len(series) == 6
    # Le dernier bucket contient l'échantillon qu'on vient de pousser.
    last = series[-1]
    assert last["rpm"] > 0
    assert last["error_rate"] == 5.0


def _ctx(db, config, warn=None, crit=None):
    return CheckContext(
        hostname_or_ip="localhost", timeout_seconds=5,
        warning_threshold=warn, critical_threshold=crit, config=config, db=db,
    )


def test_apm_check_error_rate(client, db):
    _ingest(client, app="crm", requests=100, errors=20, latency=100)  # 20 % d'erreurs
    res = ApmCheck().run(_ctx(db, {"app": "crm", "metric": "error_rate"}, warn=5, crit=10))
    assert res.status.value == "CRITICAL"
    assert res.value == 20.0

    _ingest(client, app="crm-ok", requests=100, errors=1)  # 1 %
    res = ApmCheck().run(_ctx(db, {"app": "crm-ok", "metric": "error_rate"}, warn=5, crit=10))
    assert res.status.value == "OK"


def test_apm_check_latency_and_unknown(client, db):
    _ingest(client, app="erp", requests=50, errors=0, latency=800)
    res = ApmCheck().run(_ctx(db, {"app": "erp", "metric": "latency_ms"}, warn=500, crit=2000))
    assert res.status.value == "WARNING"

    # App sans données -> UNKNOWN
    res = ApmCheck().run(_ctx(db, {"app": "fantome", "metric": "error_rate"}))
    assert res.status.value == "UNKNOWN"


def test_apm_check_rpm_low_traffic(client, db):
    _ingest(client, app="batch", requests=15)  # 1 req/min sur 15 min
    res = ApmCheck().run(_ctx(db, {"app": "batch", "metric": "rpm"}, warn=10, crit=0.5))
    # 1 req/min <= warn(10) mais > crit(0.5) -> WARNING (débit anormalement bas)
    assert res.status.value == "WARNING"
