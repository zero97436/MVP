from fastapi.testclient import TestClient

from app.main import app


def test_public_status_no_auth(client):
    """Accessible SANS token, expose uniquement nom/catégorie/état des services métier."""
    # Service métier avec un composant OK.
    from app.models.check import Check

    bs = client.post("/api/bam", json={"name": "Site public", "category": "Web", "icon": "globe"}).json()
    host = client.post("/api/hosts", json={"name": "pub-h", "hostname_or_ip": "10.0.7.1"}).json()["id"]
    cid = client.post("/api/checks", json={"host_id": host, "name": "ping", "type": "ping"}).json()["id"]
    client.post(f"/api/bam/{bs['id']}/components", json={"check_id": cid})

    anonymous = TestClient(app)  # aucun header Authorization
    r = anonymous.get("/api/public/status")
    assert r.status_code == 200
    data = r.json()
    assert data["overall"] in ("OK", "WARNING", "CRITICAL", "UNKNOWN")
    site = next(s for s in data["services"] if s["name"] == "Site public")
    assert site["category"] == "Web"
    # Aucune fuite technique : pas de composants, hôtes, checks ni ids.
    assert "components" not in site and "id" not in site


def test_public_status_reflects_outage(client, db):
    from app.models.check import Check

    bs = client.post("/api/bam", json={"name": "Service KO", "category": "Web"}).json()
    host = client.post("/api/hosts", json={"name": "pub-ko", "hostname_or_ip": "10.0.7.2"}).json()["id"]
    cid = client.post("/api/checks", json={"host_id": host, "name": "ping", "type": "ping"}).json()["id"]
    db.get(Check, cid).last_status = "CRITICAL"
    db.commit()
    client.post(f"/api/bam/{bs['id']}/components", json={"check_id": cid})

    data = TestClient(app).get("/api/public/status").json()
    assert data["overall"] == "CRITICAL"
    ko = next(s for s in data["services"] if s["name"] == "Service KO")
    assert ko["status"] == "CRITICAL"
    # Les services en panne remontent en tête de liste.
    assert data["services"][0]["status"] == "CRITICAL"


def test_public_status_can_be_disabled(client, monkeypatch):
    from app.core.config import settings as cfg

    monkeypatch.setattr(cfg, "STATUS_PAGE_ENABLED", False)
    assert TestClient(app).get("/api/public/status").status_code == 404
