def test_ingest_and_alert_on_process_count(client):
    host_id = client.post(
        "/api/hosts", json={"name": "ex-host", "hostname_or_ip": "10.0.0.190"}
    ).json()["id"]
    # Ingestion avec les nouvelles métriques.
    r = client.post("/api/metrics/ingest", json={
        "host_id": host_id, "cpu_percent": 10, "process_count": 450, "load1": 3.2, "temperature": 55,
    })
    assert r.status_code == 201
    assert r.json()["process_count"] == 450

    latest = client.get(f"/api/metrics/hosts/{host_id}/latest", headers=client.headers).json()
    assert latest["load1"] == 3.2 and latest["temperature"] == 55

    # Check de seuil sur le nombre de processus.
    check_id = client.post("/api/checks", json={
        "host_id": host_id, "name": "Processus", "type": "metric",
        "warning_threshold": 300, "critical_threshold": 400,
        "config_json": {"metric": "process_count"},
    }).json()["id"]
    res = client.post(f"/api/checks/{check_id}/run").json()
    assert res["status"] == "CRITICAL"  # 450 >= 400
