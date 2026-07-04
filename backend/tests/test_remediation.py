from app.models.alert import Alert
from app.models.remediation_log import RemediationLog
from app.services.remediation_service import RemediationService


def _make_alert(client, db) -> int:
    host_id = client.post(
        "/api/hosts", json={"name": "rem-host", "hostname_or_ip": "10.0.0.80"}
    ).json()["id"]
    check_id = client.post(
        "/api/checks", json={"host_id": host_id, "name": "rem-check", "type": "ping"}
    ).json()["id"]
    alert = Alert(check_id=check_id, status="CRITICAL", message="down", is_active=True)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert.id


def test_rerun_check_remediation(client, db):
    alert_id = _make_alert(client, db)
    resp = client.post(
        f"/api/dashboard/incidents/{alert_id}/remediate", json={"action": "rerun_check"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    # Journalisé
    assert db.query(RemediationLog).filter_by(alert_id=alert_id, action="rerun_check").count() == 1


def test_acknowledge_remediation(client, db):
    alert_id = _make_alert(client, db)
    resp = client.post(
        f"/api/dashboard/incidents/{alert_id}/remediate", json={"action": "acknowledge"}
    )
    assert resp.status_code == 200
    assert db.get(Alert, alert_id).acknowledged is True


def test_unknown_action_rejected(client, db):
    alert_id = _make_alert(client, db)
    resp = client.post(
        f"/api/dashboard/incidents/{alert_id}/remediate", json={"action": "rm_rf_slash"}
    )
    assert resp.status_code == 400


def test_remediate_404(client):
    assert client.post(
        "/api/dashboard/incidents/99999/remediate", json={"action": "rerun_check"}
    ).status_code == 404


def test_available_actions_whitelist(db):
    ids = {a["id"] for a in RemediationService(db).available()}
    assert ids == {"rerun_check", "acknowledge", "escalate", "agent_top_processes"}
