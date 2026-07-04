from datetime import datetime, timedelta, timezone

from app.models.alert import Alert
from app.models.check_result import CheckResult


def test_sla_per_host(client, db):
    host_id = client.post(
        "/api/hosts", json={"name": "sla-host", "hostname_or_ip": "10.0.0.160"}
    ).json()["id"]
    check_id = client.post(
        "/api/checks", json={"host_id": host_id, "name": "c", "type": "ping"}
    ).json()["id"]
    now = datetime.now(timezone.utc)
    # 3 OK + 1 CRITICAL -> 75 %
    for st in ("OK", "OK", "OK", "CRITICAL"):
        db.add(CheckResult(check_id=check_id, status=st, checked_at=now))
    db.commit()

    data = client.get("/api/reports/sla", params={"days": 30}).json()
    mine = next(h for h in data["hosts"] if h["host_id"] == host_id)
    assert mine["availability"] == 75.0
    assert mine["samples"] == 4


def test_mttr(client, db):
    host_id = client.post(
        "/api/hosts", json={"name": "mttr-host", "hostname_or_ip": "10.0.0.161"}
    ).json()["id"]
    check_id = client.post(
        "/api/checks", json={"host_id": host_id, "name": "c", "type": "ping"}
    ).json()["id"]
    now = datetime.now(timezone.utc)
    # Incident résolu en 600 s.
    db.add(Alert(check_id=check_id, status="CRITICAL", is_active=False,
                 created_at=now - timedelta(seconds=700), resolved_at=now - timedelta(seconds=100)))
    # Incident toujours actif.
    db.add(Alert(check_id=check_id, status="WARNING", is_active=True, created_at=now))
    db.commit()

    data = client.get("/api/reports/mttr", params={"days": 30}).json()
    assert data["resolved"] >= 1
    assert data["active"] >= 1
    assert data["mttr_seconds"] is not None and data["mttr_seconds"] > 0


def test_report_pdf_export(client):
    resp = client.get("/api/reports/pdf", params={"days": 30})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"  # en-tête PDF valide
