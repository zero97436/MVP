from datetime import datetime, timedelta, timezone

from app.models.alert import Alert
from app.models.check import Check
from app.services.alert_service import AlertService
from app.services.maintenance_service import MaintenanceService


def _make_check(client) -> int:
    host_id = client.post(
        "/api/hosts", json={"name": "mw-host", "hostname_or_ip": "10.0.0.140"}
    ).json()["id"]
    return client.post(
        "/api/checks", json={"host_id": host_id, "name": "c", "type": "ping"}
    ).json()["id"], host_id


def test_maintenance_suppresses_alert(client, db):
    check_id, host_id = _make_check(client)
    now = datetime.now(timezone.utc)
    # Fenêtre active couvrant l'hôte.
    client.post("/api/maintenances", json={
        "host_id": host_id, "reason": "MAJ",
        "starts_at": (now - timedelta(minutes=5)).isoformat(),
        "ends_at": (now + timedelta(hours=1)).isoformat(),
    })
    check = db.get(Check, check_id)
    AlertService(db).handle_status_change(check, "CRITICAL", "OK", "down")
    # Aucune alerte ouverte pendant la maintenance.
    assert db.query(Alert).filter_by(check_id=check_id).count() == 0


def test_alert_opens_without_maintenance(client, db):
    check_id, _ = _make_check(client)
    check = db.get(Check, check_id)
    AlertService(db).handle_status_change(check, "CRITICAL", "OK", "down")
    assert db.query(Alert).filter_by(check_id=check_id).count() == 1


def test_maintenance_crud_and_validation(client):
    now = datetime.now(timezone.utc)
    # Fin avant début -> 400
    bad = client.post("/api/maintenances", json={
        "starts_at": now.isoformat(), "ends_at": (now - timedelta(hours=1)).isoformat(),
    })
    assert bad.status_code == 400
    # Création globale OK
    resp = client.post("/api/maintenances", json={
        "reason": "global", "starts_at": now.isoformat(),
        "ends_at": (now + timedelta(hours=2)).isoformat(),
    })
    assert resp.status_code == 201
    mw_id = resp.json()["id"]
    assert any(m["id"] == mw_id for m in client.get("/api/maintenances").json())
    assert client.delete(f"/api/maintenances/{mw_id}").status_code == 204
