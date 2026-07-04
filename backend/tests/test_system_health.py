from app.services.system_health_service import SystemHealthService


def test_health_structure(client, db):
    data = client.get("/api/admin/system").json()
    assert data["status"] in ("ok", "degraded")
    for comp in ("database", "redis", "celery_workers", "scheduler"):
        assert comp in data["components"]
        assert "ok" in data["components"][comp]


def test_database_component_ok(db):
    # La base de test est joignable -> composant DB ok.
    res = SystemHealthService(db)._db()
    assert res["ok"] is True
    assert "latency_ms" in res


def test_scheduler_ok_when_no_active_checks(db):
    # Sans check actif, le scheduler n'est pas considéré en panne.
    res = SystemHealthService(db)._scheduler()
    assert res["ok"] is True
