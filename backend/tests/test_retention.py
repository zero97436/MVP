from datetime import datetime, timedelta, timezone

from app.models.check_result import CheckResult
from app.models.host_metric import HostMetric
from app.services.retention_service import RetentionService


def test_purge_removes_only_old_rows(client, db):
    host_id = client.post(
        "/api/hosts", json={"name": "ret-host", "hostname_or_ip": "10.0.0.40"}
    ).json()["id"]
    check_id = client.post(
        "/api/checks", json={"host_id": host_id, "name": "ret-check", "type": "ping"}
    ).json()["id"]

    now = datetime.now(timezone.utc)
    old = now - timedelta(days=400)
    cutoff = now - timedelta(days=60)
    db.add(CheckResult(check_id=check_id, status="OK", checked_at=now))  # récent
    db.add(CheckResult(check_id=check_id, status="OK", checked_at=old))  # vieux
    db.add(HostMetric(host_id=host_id, cpu_percent=5, collected_at=now))  # récent
    db.add(HostMetric(host_id=host_id, cpu_percent=5, collected_at=old))  # vieux
    db.commit()

    deleted = RetentionService(db).purge()
    assert deleted["check_results"] >= 1
    assert deleted["host_metrics"] >= 1

    # Plus aucune ligne ancienne, et la ligne récente subsiste, pour notre check/hôte.
    assert (
        db.query(CheckResult)
        .filter(CheckResult.check_id == check_id, CheckResult.checked_at < cutoff)
        .count()
        == 0
    )
    assert (
        db.query(CheckResult)
        .filter(CheckResult.check_id == check_id, CheckResult.checked_at >= cutoff)
        .count()
        >= 1
    )
    assert (
        db.query(HostMetric)
        .filter(HostMetric.host_id == host_id, HostMetric.collected_at < cutoff)
        .count()
        == 0
    )


def test_stats_and_admin_endpoints(client):
    stats = client.get("/api/admin/stats").json()
    assert "check_results" in stats and "retention_days" in stats

    run = client.post("/api/admin/retention/run").json()
    assert "deleted" in run and "total" in run
