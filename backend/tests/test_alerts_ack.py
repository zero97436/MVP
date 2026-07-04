from app.models.alert import Alert


def _make_active_alert(client, db) -> int:
    host_id = client.post(
        "/api/hosts", json={"name": "ack-host", "hostname_or_ip": "10.0.0.20"}
    ).json()["id"]
    check_id = client.post(
        "/api/checks",
        json={"host_id": host_id, "name": "ack-check", "type": "ping"},
    ).json()["id"]
    alert = Alert(check_id=check_id, status="CRITICAL", message="down", is_active=True)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert.id


def test_acknowledge_and_unacknowledge(client, db):
    alert_id = _make_active_alert(client, db)

    # Acquittement
    resp = client.post(f"/api/dashboard/incidents/{alert_id}/ack")
    assert resp.status_code == 200
    body = resp.json()
    assert body["acknowledged"] is True
    assert body["acknowledged_by"] == "admin@local"
    assert body["acknowledged_at"] is not None

    # Visible dans la liste des incidents
    incidents = client.get("/api/dashboard/incidents").json()
    acked = next(i for i in incidents if i["alert_id"] == alert_id)
    assert acked["acknowledged"] is True

    # Retrait de l'acquittement
    resp = client.post(f"/api/dashboard/incidents/{alert_id}/unack")
    assert resp.status_code == 200
    assert resp.json()["acknowledged"] is False


def test_acknowledge_missing_alert(client):
    assert client.post("/api/dashboard/incidents/99999/ack").status_code == 404
