import app.core.license as lic
from app.models.audit_log import AuditLog


def test_audit_records_writes_with_user(client, db):
    """Une écriture API est tracée : utilisateur, action, code, chemin."""
    before = db.query(AuditLog).count()
    client.post("/api/hosts", json={"name": "audited", "hostname_or_ip": "10.0.0.99"})

    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(5).all()
    assert db.query(AuditLog).count() > before
    entry = next(r for r in rows if r.action == "hosts:create")
    assert entry.user_email == "admin@local"
    assert entry.method == "POST" and entry.status_code == 201
    assert entry.path == "/api/hosts"


def test_audit_ignores_reads_and_machine_endpoints(client, db):
    before = db.query(AuditLog).count()
    client.get("/api/hosts")                       # lecture -> pas d'audit
    client.post("/api/metrics/ingest", json={})    # machine-à-machine -> exclu
    assert db.query(AuditLog).count() == before


def test_audit_action_naming(client, db):
    host = client.post("/api/hosts", json={"name": "aud-2", "hostname_or_ip": "10.0.0.98"}).json()["id"]
    client.delete(f"/api/hosts/{host}")
    client.post("/api/auth/login", json={"email": "admin@local", "password": "admin1234"})

    actions = [r.action for r in db.query(AuditLog).order_by(AuditLog.id.desc()).limit(10)]
    assert "hosts:delete" in actions
    assert "auth:login" in actions


def test_audit_route_filters(client):
    client.post("/api/hosts", json={"name": "aud-3", "hostname_or_ip": "10.0.0.97"})
    rows = client.get("/api/audit", params={"user": "admin", "q": "hosts"}).json()
    assert rows and all("hosts" in r["path"] for r in rows)
    assert all("admin" in (r["user_email"] or "") for r in rows)


def test_audit_disabled_without_enterprise(client, db, monkeypatch):
    monkeypatch.setattr(lic, "get_license", lambda: {
        "plan": "business", "max_hosts": None,
        "features": sorted(lic.PLAN_FEATURES["business"]), "customer": None, "expires": None,
    })
    # Plus d'enregistrement…
    before = db.query(AuditLog).count()
    client.post("/api/hosts", json={"name": "aud-4", "hostname_or_ip": "10.0.0.96"})
    assert db.query(AuditLog).count() == before
    # …et consultation refusée avec message d'upgrade.
    r = client.get("/api/audit")
    assert r.status_code == 403 and "Enterprise" in r.json()["detail"]
