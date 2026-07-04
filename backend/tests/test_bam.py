from app.models.check import Check


def _make_check(client, db, status: str) -> int:
    host_id = client.post("/api/hosts", json={"name": f"h-{status}-x", "hostname_or_ip": f"10.0.1.{hash(status) % 200}"}).json()["id"]
    cid = client.post("/api/checks", json={"host_id": host_id, "name": "c", "type": "ping"}).json()["id"]
    c = db.get(Check, cid)
    c.last_status = status
    db.commit()
    return cid


def test_bam_worst_rule(client, db):
    ok = _make_check(client, db, "OK")
    crit = _make_check(client, db, "CRITICAL")
    bs = client.post("/api/bam", json={"name": "Site e-commerce", "rule": "worst"}).json()
    client.post(f"/api/bam/{bs['id']}/components", json={"check_id": ok})
    client.post(f"/api/bam/{bs['id']}/components", json={"check_id": crit})

    services = client.get("/api/bam").json()
    svc = next(s for s in services if s["id"] == bs["id"])
    assert svc["status"] == "CRITICAL"  # pire des composants
    assert svc["total"] == 2 and svc["ok_count"] == 1


def test_bam_percent_rule(client, db):
    bs = client.post("/api/bam", json={
        "name": "Cluster", "rule": "percent", "warning_threshold": 100, "critical_threshold": 50,
    }).json()
    for st in ("OK", "OK", "OK", "CRITICAL"):  # 75% OK
        client.post(f"/api/bam/{bs['id']}/components", json={"check_id": _make_check(client, db, st)})
    svc = next(s for s in client.get("/api/bam").json() if s["id"] == bs["id"])
    # 75% < 100 (warn) et >= 50 (crit) -> WARNING
    assert svc["status"] == "WARNING"


def test_bam_crud_validation(client):
    assert client.post("/api/bam", json={"name": "X", "rule": "bogus"}).status_code == 400
    bs = client.post("/api/bam", json={"name": "Svc"}).json()
    assert client.post(f"/api/bam/{bs['id']}/components", json={}).status_code == 400
    assert client.delete(f"/api/bam/{bs['id']}").status_code == 204


def test_bam_category_and_icon(client):
    bs = client.post("/api/bam", json={"name": "Boutique", "category": "Applications métier", "icon": "cart"}).json()
    svc = next(s for s in client.get("/api/bam").json() if s["id"] == bs["id"])
    assert svc["category"] == "Applications métier"
    assert svc["icon"] == "cart"
    assert svc["pos_x"] is None and svc["pos_y"] is None


def test_bam_layout_drag_and_drop(client):
    a = client.post("/api/bam", json={"name": "Tuile A"}).json()["id"]
    b = client.post("/api/bam", json={"name": "Tuile B"}).json()["id"]

    # Enregistre des positions libres (drag & drop).
    r = client.post("/api/bam/layout", json={"positions": [
        {"id": a, "pos_x": 120, "pos_y": 40},
        {"id": b, "pos_x": 360, "pos_y": 220},
    ]})
    assert r.status_code == 200 and r.json()["updated"] == 2

    svcs = {s["id"]: s for s in client.get("/api/bam").json()}
    assert (svcs[a]["pos_x"], svcs[a]["pos_y"]) == (120, 40)
    assert (svcs[b]["pos_x"], svcs[b]["pos_y"]) == (360, 220)

    # Réinitialisation (retour au placement auto).
    client.post("/api/bam/layout", json={"positions": [{"id": a, "pos_x": None, "pos_y": None}]})
    assert client.get("/api/bam").json()
    reset = next(s for s in client.get("/api/bam").json() if s["id"] == a)
    assert reset["pos_x"] is None and reset["pos_y"] is None


def test_bam_patch_update(client):
    bs = client.post("/api/bam", json={"name": "Old", "category": "Général"}).json()["id"]
    r = client.patch(f"/api/bam/{bs}", json={"name": "Nouveau", "category": "Infrastructure", "icon": "cloud"})
    assert r.status_code == 200
    svc = next(s for s in client.get("/api/bam").json() if s["id"] == bs)
    assert svc["name"] == "Nouveau" and svc["category"] == "Infrastructure" and svc["icon"] == "cloud"
