def _make_host(client) -> int:
    return client.post(
        "/api/hosts", json={"name": "mc-host", "hostname_or_ip": "10.0.0.30"}
    ).json()["id"]


def test_metric_check_triggers_critical(client):
    host_id = _make_host(client)
    # Pousse une métrique CPU élevée.
    client.post("/api/metrics/ingest", json={"host_id": host_id, "cpu_percent": 95})

    check_id = client.post(
        "/api/checks",
        json={
            "host_id": host_id,
            "name": "CPU élevé",
            "type": "metric",
            "warning_threshold": 80,
            "critical_threshold": 90,
            "config_json": {"metric": "cpu_percent"},
        },
    ).json()["id"]

    res = client.post(f"/api/checks/{check_id}/run").json()
    assert res["status"] == "CRITICAL"
    assert res["value"] == 95.0

    # Un incident actif doit exister.
    incidents = client.get("/api/dashboard/incidents").json()
    assert any(i["check_id"] == check_id for i in incidents)


def test_metric_check_ok_and_unknown(client):
    host_id = _make_host(client)
    check_id = client.post(
        "/api/checks",
        json={
            "host_id": host_id,
            "name": "CPU",
            "type": "metric",
            "warning_threshold": 80,
            "critical_threshold": 90,
            "config_json": {"metric": "cpu_percent"},
        },
    ).json()["id"]

    # Sans métrique -> UNKNOWN
    assert client.post(f"/api/checks/{check_id}/run").json()["status"] == "UNKNOWN"

    # Métrique basse -> OK
    client.post("/api/metrics/ingest", json={"host_id": host_id, "cpu_percent": 10})
    assert client.post(f"/api/checks/{check_id}/run").json()["status"] == "OK"
