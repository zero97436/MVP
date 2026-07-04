def test_layout_default(client):
    data = client.get("/api/dashboard/layout").json()
    assert data["custom"] is False
    ids = [s["id"] for s in data["sections"]]
    assert ids == ["hero", "kpi", "incidents", "trend", "fleet"]
    assert all(s["visible"] for s in data["sections"])


def test_layout_save_reorder_and_hide(client):
    payload = {"sections": [
        {"id": "incidents", "visible": True},
        {"id": "hero", "visible": True},
        {"id": "kpi", "visible": False},
        {"id": "trend", "visible": True},
        {"id": "fleet", "visible": False},
    ]}
    r = client.put("/api/dashboard/layout", json=payload)
    assert r.status_code == 200 and r.json()["custom"] is True

    data = client.get("/api/dashboard/layout").json()
    assert data["custom"] is True
    ids = [s["id"] for s in data["sections"]]
    assert ids[0] == "incidents"  # ordre personnalisé conservé
    hidden = {s["id"] for s in data["sections"] if not s["visible"]}
    assert hidden == {"kpi", "fleet"}


def test_layout_ignores_unknown_sections(client):
    r = client.put("/api/dashboard/layout", json={"sections": [
        {"id": "hero", "visible": True},
        {"id": "bogus", "visible": True},
    ]})
    ids = [s["id"] for s in r.json()["sections"]]
    assert "bogus" not in ids

    # que des sections inconnues -> 400
    assert client.put("/api/dashboard/layout", json={"sections": [{"id": "nope"}]}).status_code == 400


def test_layout_reset(client):
    client.put("/api/dashboard/layout", json={"sections": [{"id": "fleet", "visible": True}]})
    assert client.delete("/api/dashboard/layout").status_code == 204
    assert client.get("/api/dashboard/layout").json()["custom"] is False
