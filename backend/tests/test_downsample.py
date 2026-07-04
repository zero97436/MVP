from datetime import datetime, timedelta, timezone

from app.models.host_metric import HostMetric
from app.services.downsample_service import DownsampleService


def test_rollup_aggregates_by_hour(client, db):
    host_id = client.post(
        "/api/hosts", json={"name": "ds-host", "hostname_or_ip": "10.0.0.50"}
    ).json()["id"]

    # Deux échantillons dans la MÊME heure (il y a ~90 min, dans la fenêtre de 48h).
    base = (datetime.now(timezone.utc) - timedelta(minutes=90)).replace(minute=0, second=0, microsecond=0)
    db.add(HostMetric(host_id=host_id, cpu_percent=20, disk_percent=50, collected_at=base + timedelta(minutes=5)))
    db.add(HostMetric(host_id=host_id, cpu_percent=40, disk_percent=60, collected_at=base + timedelta(minutes=35)))
    db.commit()

    written = DownsampleService(db).rollup()
    assert written >= 1

    rollups = DownsampleService(db).for_host(host_id, days=7)
    mine = [r for r in rollups if r.host_id == host_id]
    assert len(mine) == 1
    r = mine[0]
    assert r.cpu_avg == 30.0   # (20+40)/2
    assert r.cpu_max == 40.0
    assert r.sample_count == 2


def test_rollup_endpoint(client):
    host_id = client.post(
        "/api/hosts", json={"name": "ds-host2", "hostname_or_ip": "10.0.0.51"}
    ).json()["id"]
    client.post("/api/metrics/ingest", json={"host_id": host_id, "cpu_percent": 12})

    # Déclenche le rollup via l'endpoint admin
    assert client.post("/api/admin/rollup/run").json()["buckets_written"] >= 1
    # Lecture des rollups
    assert client.get(f"/api/metrics/hosts/{host_id}/hourly?days=7").status_code == 200
