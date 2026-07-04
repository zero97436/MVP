def test_search_all_types(client):
    host = client.post("/api/hosts", json={"name": "srv-recherche", "hostname_or_ip": "10.0.6.1"}).json()["id"]
    client.post("/api/checks", json={"host_id": host, "name": "recherche-http", "type": "http"})
    client.post("/api/tickets", json={"title": "srv-recherche : disque plein"})

    data = client.get("/api/search", params={"q": "recherche"}).json()
    assert any(h["name"] == "srv-recherche" for h in data["hosts"])
    chk = next(c for c in data["checks"] if c["name"] == "recherche-http")
    assert chk["host_name"] == "srv-recherche"
    assert any("disque plein" in t["title"] for t in data["tickets"])


def test_search_by_ip_and_min_length(client):
    client.post("/api/hosts", json={"name": "ip-cible", "hostname_or_ip": "192.168.77.42"})
    data = client.get("/api/search", params={"q": "192.168.77"}).json()
    assert any(h["hostname_or_ip"] == "192.168.77.42" for h in data["hosts"])

    # Moins de 2 caractères -> vide (pas de scan complet).
    data = client.get("/api/search", params={"q": "x"}).json()
    assert data == {"hosts": [], "checks": [], "tickets": [], "events": []}


def test_search_limit(client):
    for i in range(8):
        client.post("/api/hosts", json={"name": f"bulk-search-{i}", "hostname_or_ip": f"10.0.66.{i}"})
    data = client.get("/api/search", params={"q": "bulk-search"}).json()
    assert len(data["hosts"]) == 5  # limité à 5 par type
