"""Mode de supervision par hôte : agentless / agent (push) / ssh (tunnel)."""


def _create(client, **extra):
    body = {"name": "h", "hostname_or_ip": "10.0.0.9"}
    body.update(extra)
    return client.post("/api/hosts", json=body)


def test_default_mode_is_agentless(client):
    r = _create(client)
    assert r.status_code == 201
    assert r.json()["monitoring_mode"] == "agentless"


def test_invalid_mode_rejected(client):
    r = _create(client, monitoring_mode="carrier-pigeon")
    assert r.status_code == 422


def test_agent_mode_enrollment(client):
    host = _create(client, monitoring_mode="agent").json()
    r = client.get(f"/api/hosts/{host['id']}/enrollment")
    assert r.status_code == 200
    data = r.json()
    assert data["monitoring_mode"] == "agent"
    # La commande cible le bon hôte et l'endpoint d'ingestion.
    assert f"--host-id {host['id']}" in data["install_command"]
    assert "/metrics/ingest" in data["install_command"]
    assert "systemd" in data["systemd_unit"].lower() or "[Service]" in data["systemd_unit"]


def test_ssh_config_password_is_redacted(client):
    host = _create(
        client,
        monitoring_mode="ssh",
        ssh_config={"port": 2222, "user": "ops", "password": "s3cret"},
    ).json()
    # Le mot de passe n'est jamais renvoyé en clair.
    assert host["ssh_config"]["password"] == "********"
    assert host["ssh_config"]["user"] == "ops"
    assert host["ssh_config"]["port"] == 2222

    # Rechargé : toujours masqué, jamais le clair.
    again = client.get(f"/api/hosts/{host['id']}").json()
    assert again["ssh_config"]["password"] == "********"

    # Mise à jour partielle (mot de passe masqué conservé) : ne casse pas le secret.
    upd = client.put(f"/api/hosts/{host['id']}", json={"description": "edit"})
    assert upd.status_code == 200
    assert upd.json()["ssh_config"]["password"] == "********"


def test_ssh_defaults_merged_into_check_config(client, db):
    """Un check ssh_command hérite des identifiants SSH de l'hôte (mode ssh)."""
    from app.core.crypto import decrypt_config
    from app.models.check import Check
    from app.models.host import Host

    host = _create(
        client, monitoring_mode="ssh",
        ssh_config={"port": 2200, "user": "svc", "password": "pw"},
    ).json()
    h = db.get(Host, host["id"])
    chk = Check(host_id=h.id, name="c", type="ssh_command",
                config_json={"command": "uptime"}, is_active=True)
    db.add(chk)
    db.commit()

    # Reproduit la fusion faite par CheckService.run_check.
    cfg = decrypt_config(chk.config_json or {})
    if h.monitoring_mode == "ssh" and h.ssh_config:
        shared = decrypt_config(h.ssh_config)
        defaults = {k: shared[k] for k in ("port", "user", "password") if shared.get(k)}
        cfg = {**defaults, **cfg}
    assert cfg["user"] == "svc"
    assert cfg["port"] == 2200
    assert cfg["password"] == "pw"
    assert cfg["command"] == "uptime"
