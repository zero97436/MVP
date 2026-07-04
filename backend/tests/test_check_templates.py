def test_templates_default_seed(client):
    templates = client.get("/api/check-templates").json()
    names = [t["name"] for t in templates]
    assert "Serveur Linux" in names
    assert "Serveur Web (HTTPS)" in names
    linux = next(t for t in templates if t["name"] == "Serveur Linux")
    assert [i["type"] for i in linux["items"]] == ["ping", "tcp_port"]


def test_template_apply_and_dedupe(client):
    host = client.post("/api/hosts", json={"name": "tpl-host", "hostname_or_ip": "10.0.8.1"}).json()["id"]
    linux = next(t for t in client.get("/api/check-templates").json() if t["name"] == "Serveur Linux")

    r = client.post(f"/api/check-templates/{linux['id']}/apply", json={"host_id": host}).json()
    assert sorted(r["created"]) == ["Ping", "SSH (22)"]
    assert r["skipped"] == []

    # Ré-appliquer -> tout est ignoré (anti-doublon par nom).
    r2 = client.post(f"/api/check-templates/{linux['id']}/apply", json={"host_id": host}).json()
    assert r2["created"] == [] and sorted(r2["skipped"]) == ["Ping", "SSH (22)"]

    # Les checks existent bien sur l'hôte, avec la config du modèle.
    checks = client.get("/api/checks", params={"host_id": host}).json()
    ssh = next(c for c in checks if c["name"] == "SSH (22)")
    assert ssh["type"] == "tcp_port" and ssh["config_json"]["port"] == 22


def test_template_from_host(client):
    host = client.post("/api/hosts", json={"name": "modele-src", "hostname_or_ip": "10.0.8.2"}).json()["id"]
    client.post("/api/checks", json={"host_id": host, "name": "Ping custom", "type": "ping", "interval_seconds": 30})
    client.post("/api/checks", json={"host_id": host, "name": "API interne", "type": "tcp_port",
                                     "config_json": {"port": 9000}, "warning_threshold": 100})

    tpl = client.post("/api/check-templates/from-host",
                      json={"host_id": host, "name": "Mon serveur type", "description": "capture"}).json()
    assert len(tpl["items"]) == 2
    api_item = next(i for i in tpl["items"] if i["name"] == "API interne")
    assert api_item["config_json"]["port"] == 9000
    assert api_item["warning_threshold"] == 100

    # Application sur un autre hôte.
    other = client.post("/api/hosts", json={"name": "clone", "hostname_or_ip": "10.0.8.3"}).json()["id"]
    r = client.post(f"/api/check-templates/{tpl['id']}/apply", json={"host_id": other}).json()
    assert len(r["created"]) == 2


def test_template_validation(client):
    # Type de check inconnu filtré ; aucun item valide -> 400.
    assert client.post("/api/check-templates", json={"name": "vide", "items": [
        {"name": "X", "type": "bogus"}]}).status_code == 400
    # Nom déjà pris -> 400.
    assert client.post("/api/check-templates", json={"name": "Serveur Linux", "items": [
        {"name": "Ping", "type": "ping"}]}).status_code == 400
    # Hôte inexistant -> 404.
    tpl = client.get("/api/check-templates").json()[0]
    assert client.post(f"/api/check-templates/{tpl['id']}/apply", json={"host_id": 99999}).status_code == 404


def test_template_delete(client):
    tpl = client.post("/api/check-templates", json={"name": "a-suppr", "items": [
        {"name": "Ping", "type": "ping"}]}).json()
    assert client.delete(f"/api/check-templates/{tpl['id']}").status_code == 204
    assert client.delete(f"/api/check-templates/{tpl['id']}").status_code == 404
