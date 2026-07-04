from app.models.check import Check
from app.services.alert_service import AlertService


def test_child_alert_suppressed_when_parent_down(client, db):
    # Parent avec un check CRITICAL.
    parent = client.post("/api/hosts", json={"name": "switch", "hostname_or_ip": "10.0.3.1"}).json()["id"]
    pchk = client.post("/api/checks", json={"host_id": parent, "name": "ping", "type": "ping"}).json()["id"]
    db.get(Check, pchk).last_status = "CRITICAL"
    db.commit()

    # Enfant qui dépend du parent.
    child = client.post("/api/hosts", json={"name": "serveur", "hostname_or_ip": "10.0.3.2", "parent_host_id": parent}).json()["id"]
    cchk = client.post("/api/checks", json={"host_id": child, "name": "ping", "type": "ping"}).json()["id"]

    from app.models.alert import Alert
    AlertService(db).handle_status_change(db.get(Check, cchk), "CRITICAL", "OK", "down")
    # Aucune alerte : le parent est en panne -> enfant injoignable, pas d'alerte.
    assert db.query(Alert).filter_by(check_id=cchk).count() == 0


def test_child_alert_opens_when_parent_ok(client, db):
    parent = client.post("/api/hosts", json={"name": "switch2", "hostname_or_ip": "10.0.3.10"}).json()["id"]
    pchk = client.post("/api/checks", json={"host_id": parent, "name": "ping", "type": "ping"}).json()["id"]
    db.get(Check, pchk).last_status = "OK"
    db.commit()

    child = client.post("/api/hosts", json={"name": "srv2", "hostname_or_ip": "10.0.3.11", "parent_host_id": parent}).json()["id"]
    cchk = client.post("/api/checks", json={"host_id": child, "name": "ping", "type": "ping"}).json()["id"]

    from app.models.alert import Alert
    AlertService(db).handle_status_change(db.get(Check, cchk), "CRITICAL", "OK", "down")
    assert db.query(Alert).filter_by(check_id=cchk).count() == 1


def test_host_geo_persisted(client):
    h = client.post("/api/hosts", json={
        "name": "geo-h", "hostname_or_ip": "10.0.5.1",
        "location": "Agence Paris", "latitude": 48.8566, "longitude": 2.3522,
    }).json()
    assert h["location"] == "Agence Paris"
    assert h["latitude"] == 48.8566 and h["longitude"] == 2.3522

    # Mise à jour / effacement des coordonnées.
    upd = client.put(f"/api/hosts/{h['id']}", json={"latitude": 45.75, "longitude": 4.85}).json()
    assert upd["latitude"] == 45.75


def test_host_parent_persisted(client):
    parent = client.post("/api/hosts", json={"name": "p", "hostname_or_ip": "10.0.3.20"}).json()["id"]
    child = client.post("/api/hosts", json={"name": "e", "hostname_or_ip": "10.0.3.21", "parent_host_id": parent}).json()
    assert child["parent_host_id"] == parent
