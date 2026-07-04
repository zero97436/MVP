from datetime import datetime, timedelta, timezone

from app.models.alert import Alert
from app.models.check import Check
from app.models.check_result import CheckResult
from app.services.alert_service import AlertService


def _make_check(client, ip):
    host = client.post("/api/hosts", json={"name": f"flap-{ip}", "hostname_or_ip": ip}).json()["id"]
    return client.post("/api/checks", json={"host_id": host, "name": "svc", "type": "ping"}).json()["id"]


def _push_results(db, check_id, statuses):
    now = datetime.now(timezone.utc)
    for i, st in enumerate(statuses):
        db.add(CheckResult(check_id=check_id, status=st,
                           checked_at=now - timedelta(seconds=(len(statuses) - i) * 30)))
    db.commit()


def test_flapping_suppresses_alert(client, db):
    """Un check qui oscille OK/CRITICAL -> alerte supprimée + événement flapping."""
    cid = _make_check(client, "10.0.4.1")
    _push_results(db, cid, ["OK", "CRITICAL"] * 10)  # 19 transitions sur 20 résultats

    AlertService(db).handle_status_change(db.get(Check, cid), "CRITICAL", "OK", "down")
    assert db.query(Alert).filter_by(check_id=cid).count() == 0

    events = client.get("/api/events", params={"type": "alert_suppressed_flapping"}).json()
    assert any(str(cid) in str(e) or "flapping" in e["message"] for e in events)


def test_stable_check_still_alerts(client, db):
    """Un check stable qui tombe -> alerte normale (pas de faux positif flapping)."""
    cid = _make_check(client, "10.0.4.2")
    _push_results(db, cid, ["OK"] * 19 + ["CRITICAL"])  # 1 seule transition

    AlertService(db).handle_status_change(db.get(Check, cid), "CRITICAL", "OK", "down")
    assert db.query(Alert).filter_by(check_id=cid).count() == 1


def test_flapping_needs_history(client, db):
    """Trop peu d'historique -> jamais considéré en flapping."""
    cid = _make_check(client, "10.0.4.3")
    _push_results(db, cid, ["OK", "CRITICAL", "OK"])  # 3 résultats seulement

    AlertService(db).handle_status_change(db.get(Check, cid), "CRITICAL", "OK", "down")
    assert db.query(Alert).filter_by(check_id=cid).count() == 1
