from datetime import datetime, timedelta, timezone

from app.models.alert import Alert
from app.services.alert_service import AlertService, _in_active_hours


def _make_alert(client, db, minutes_old: int, acknowledged=False) -> int:
    host_id = client.post("/api/hosts", json={"name": f"esc-{minutes_old}-{acknowledged}", "hostname_or_ip": f"10.0.2.{minutes_old % 200}"}).json()["id"]
    check_id = client.post("/api/checks", json={"host_id": host_id, "name": "c", "type": "ping"}).json()["id"]
    a = Alert(check_id=check_id, status="CRITICAL", message="down", is_active=True,
              acknowledged=acknowledged,
              created_at=datetime.now(timezone.utc) - timedelta(minutes=minutes_old))
    db.add(a)
    db.commit()
    db.refresh(a)
    return a.id


def test_old_unacked_alert_is_escalated(client, db):
    alert_id = _make_alert(client, db, minutes_old=30)
    AlertService(db).escalate_pending()
    assert db.get(Alert, alert_id).escalated_at is not None


def test_recent_alert_not_escalated(client, db):
    alert_id = _make_alert(client, db, minutes_old=2)
    AlertService(db).escalate_pending()
    assert db.get(Alert, alert_id).escalated_at is None


def test_acknowledged_alert_not_escalated(client, db):
    alert_id = _make_alert(client, db, minutes_old=30, acknowledged=True)
    AlertService(db).escalate_pending()
    assert db.get(Alert, alert_id).escalated_at is None


def test_active_hours_window():
    assert _in_active_hours(None) is True
    assert _in_active_hours("00:00-23:59") is True
    # Fenêtre impossible (1 minute autour d'une heure improbable) -> souvent False,
    # on teste juste que ça ne lève pas et renvoie un booléen.
    assert isinstance(_in_active_hours("03:00-03:01"), bool)
