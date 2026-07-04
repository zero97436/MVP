def test_metric_ingest_and_read(client):
    host_id = client.post(
        "/api/hosts", json={"name": "metrics-host", "hostname_or_ip": "10.0.0.9"}
    ).json()["id"]

    # Ingestion par host_id (pas de clé configurée en test -> ouvert).
    resp = client.post(
        "/api/metrics/ingest",
        json={
            "host_id": host_id,
            "cpu_percent": 42.5,
            "mem_percent": 60,
            "disk_percent": 81,
            "disks": {"C:": 81.0, "D:": 1.6},
            "net_mbps": 12,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["cpu_percent"] == 42.5
    assert resp.json()["disks"]["D:"] == 1.6

    # Ingestion par hostname_or_ip.
    assert (
        client.post(
            "/api/metrics/ingest",
            json={"hostname_or_ip": "10.0.0.9", "cpu_percent": 10},
        ).status_code
        == 201
    )

    # Lecture série.
    series = client.get(f"/api/metrics/hosts/{host_id}").json()
    assert len(series) == 2

    # Dernier point.
    latest = client.get(f"/api/metrics/hosts/{host_id}/latest").json()
    assert latest["host_id"] == host_id


def test_metric_ingest_unknown_host(client):
    resp = client.post("/api/metrics/ingest", json={"host_id": 99999, "cpu_percent": 1})
    assert resp.status_code == 404
