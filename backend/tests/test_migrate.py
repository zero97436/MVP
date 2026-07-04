CSV = """name;ip;environment;site;latitude;longitude;template;parent
Routeur agence;192.168.50.1;production;Agence Lyon;45.75;4.85;;
Serveur agence;192.168.50.10;production;Agence Lyon;;;Serveur Linux;Routeur agence
"""

NAGIOS = """
define host {
    host_name        sw-core
    alias            Switch coeur
    address          192.168.60.1
}
define host {
    host_name        web01
    alias            Serveur web
    address          192.168.60.10
    parents          sw-core
}
define service {
    host_name              web01
    service_description    HTTP
    check_command          check_http
}
define service {
    host_name              web01
    service_description    Port applicatif
    check_command          check_tcp!8443
}
define service {
    host_name              web01
    service_description    Plugin maison
    check_command          check_custom_xyz!foo
}
"""


def test_csv_dry_run_then_apply(client):
    r = client.post("/api/migrate", json={"format": "csv", "content": CSV, "dry_run": True}).json()
    assert r["dry_run"] is True
    assert len(r["hosts"]) == 2
    srv = next(h for h in r["hosts"] if h["name"] == "Serveur agence")
    assert srv["template"] == "Serveur Linux" and srv["parent"] == "Routeur agence"

    # Seed des templates par défaut (lazy) puis import réel.
    client.get("/api/check-templates")
    r = client.post("/api/migrate", json={"format": "csv", "content": CSV, "dry_run": False}).json()
    assert sorted(r["created"]) == ["Routeur agence", "Serveur agence"]
    assert r["checks_created"] == 2  # template Serveur Linux : Ping + SSH

    hosts = client.get("/api/hosts").json()
    routeur = next(h for h in hosts if h["name"] == "Routeur agence")
    serveur = next(h for h in hosts if h["name"] == "Serveur agence")
    assert serveur["parent_host_id"] == routeur["id"]      # dépendance résolue
    assert routeur["location"] == "Agence Lyon" and routeur["latitude"] == 45.75

    # Ré-import -> tout est skippé (idempotent).
    r2 = client.post("/api/migrate", json={"format": "csv", "content": CSV, "dry_run": False}).json()
    assert r2["created"] == [] and len(r2["skipped"]) == 2


def test_nagios_import(client):
    r = client.post("/api/migrate", json={"format": "nagios", "content": NAGIOS, "dry_run": False}).json()
    assert sorted(r["created"]) == ["Serveur web", "Switch coeur"]
    # Ping auto sur chaque hôte + HTTP + tcp 8443 = 4 checks ; plugin maison -> warning.
    assert r["checks_created"] == 4
    assert any("check_custom_xyz" in w for w in r["warnings"])

    hosts = client.get("/api/hosts").json()
    sw = next(h for h in hosts if h["name"] == "Switch coeur")
    web = next(h for h in hosts if h["name"] == "Serveur web")
    assert web["parent_host_id"] == sw["id"]  # parents Nagios -> dépendances

    checks = client.get("/api/checks", params={"host_id": web["id"]}).json()
    names = {c["name"]: c for c in checks}
    assert names["HTTP"]["type"] == "http"
    assert names["Port applicatif"]["type"] == "tcp_port"
    assert names["Port applicatif"]["config_json"]["port"] == 8443


def test_migrate_respects_license(client, monkeypatch):
    used = len(client.get("/api/hosts").json())
    monkeypatch.setattr("app.api.routes.hosts.get_license",
                        lambda: {"plan": "free", "max_hosts": used + 1, "customer": None, "expires": None})
    r = client.post("/api/migrate", json={"format": "csv", "dry_run": False, "content":
                                          "name,ip\na,10.9.9.1\nb,10.9.9.2\n"})
    assert r.status_code == 403


def test_migrate_bad_format(client):
    assert client.post("/api/migrate", json={"format": "zabbix", "content": "", "dry_run": True}).status_code == 400
