from app.services.event_service import EventService


def test_events_offset_pagination(client, db):
    svc = EventService(db)
    for i in range(15):
        svc.record("test_evt", f"msg {i}", commit=False)
    db.commit()

    page1 = client.get("/api/events", params={"type": "test_evt", "limit": 5, "offset": 0}).json()
    page2 = client.get("/api/events", params={"type": "test_evt", "limit": 5, "offset": 5}).json()
    assert len(page1) == 5 and len(page2) == 5
    # Pas de chevauchement entre les pages.
    ids1 = {e["id"] for e in page1}
    ids2 = {e["id"] for e in page2}
    assert ids1.isdisjoint(ids2)


def test_results_offset_pagination(client, db):
    from datetime import datetime, timezone
    from app.models.check_result import CheckResult

    host_id = client.post("/api/hosts", json={"name": "pg", "hostname_or_ip": "10.0.0.180"}).json()["id"]
    check_id = client.post("/api/checks", json={"host_id": host_id, "name": "c", "type": "ping"}).json()["id"]
    now = datetime.now(timezone.utc)
    for _ in range(8):
        db.add(CheckResult(check_id=check_id, status="OK", checked_at=now))
    db.commit()

    p1 = client.get(f"/api/checks/{check_id}/results", params={"limit": 3, "offset": 0}).json()
    p2 = client.get(f"/api/checks/{check_id}/results", params={"limit": 3, "offset": 3}).json()
    assert len(p1) == 3 and len(p2) == 3
    assert {r["id"] for r in p1}.isdisjoint({r["id"] for r in p2})
