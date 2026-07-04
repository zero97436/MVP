def test_host_crud(client):
    # Create
    resp = client.post("/api/hosts", json={"name": "srv1", "hostname_or_ip": "10.0.0.1"})
    assert resp.status_code == 201
    host_id = resp.json()["id"]

    # Read
    assert client.get(f"/api/hosts/{host_id}").status_code == 200

    # Update
    resp = client.put(f"/api/hosts/{host_id}", json={"description": "updated"})
    assert resp.json()["description"] == "updated"

    # List
    assert any(h["id"] == host_id for h in client.get("/api/hosts").json())

    # Delete
    assert client.delete(f"/api/hosts/{host_id}").status_code == 204
    assert client.get(f"/api/hosts/{host_id}").status_code == 404


def test_check_crud_and_run(client):
    host_id = client.post(
        "/api/hosts", json={"name": "srv2", "hostname_or_ip": "127.0.0.1"}
    ).json()["id"]

    resp = client.post(
        "/api/checks",
        json={
            "host_id": host_id,
            "name": "disk mock",
            "type": "disk_usage",
            "warning_threshold": 80,
            "critical_threshold": 90,
            "config_json": {"mock": True, "mock_value": 95},
        },
    )
    assert resp.status_code == 201
    check_id = resp.json()["id"]

    # Run -> doit renvoyer CRITICAL (mock_value 95 >= 90)
    run = client.post(f"/api/checks/{check_id}/run")
    assert run.status_code == 200
    assert run.json()["status"] == "CRITICAL"

    # Results history
    results = client.get(f"/api/checks/{check_id}/results")
    assert results.status_code == 200
    assert len(results.json()) >= 1


def test_dashboard_summary(client):
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert "hosts_total" in body and "status_counts" in body
