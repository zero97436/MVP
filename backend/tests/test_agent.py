from app.models.agent_command import AgentCommand
from app.models.alert import Alert


def _make_alert(client, db) -> tuple[int, int]:
    host_id = client.post(
        "/api/hosts", json={"name": "agent-host", "hostname_or_ip": "10.0.0.90"}
    ).json()["id"]
    check_id = client.post(
        "/api/checks", json={"host_id": host_id, "name": "agent-check", "type": "ping"}
    ).json()["id"]
    alert = Alert(check_id=check_id, status="CRITICAL", message="cpu high", is_active=True)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return host_id, alert.id


def test_agent_remediation_full_cycle(client, db):
    host_id, alert_id = _make_alert(client, db)

    # 1. L'opérateur déclenche l'action agent -> commande en file.
    resp = client.post(
        f"/api/dashboard/incidents/{alert_id}/remediate",
        json={"action": "agent_top_processes"},
    )
    assert resp.status_code == 200
    cmd_id = resp.json()["command_id"]
    assert db.get(AgentCommand, cmd_id).status == "pending"

    # 2. L'agent récupère ses commandes (passent en 'sent').
    poll = client.get("/api/agent/commands", params={"host_id": host_id}).json()
    assert any(c["id"] == cmd_id and c["action"] == "top_processes" for c in poll)
    assert db.get(AgentCommand, cmd_id).status == "sent"

    # 3. L'agent renvoie le résultat.
    assert client.post(
        f"/api/agent/commands/{cmd_id}/result",
        json={"status": "done", "result": "Top: chrome 40%"},
    ).status_code == 200

    # 4. L'UI lit le résultat.
    got = client.get(f"/api/agent/commands/{cmd_id}").json()
    assert got["status"] == "done"
    assert "chrome" in got["result"]


def test_agent_poll_unknown_host(client):
    assert client.get("/api/agent/commands", params={"host_id": 99999}).status_code == 404


def test_agent_probe_assigned_checks_and_result(client, db):
    # Hôte-sonde (qui exécute) + hôte-cible (à surveiller).
    prober = client.post(
        "/api/hosts", json={"name": "probe", "hostname_or_ip": "10.0.0.100"}
    ).json()["id"]
    target = client.post(
        "/api/hosts", json={"name": "cible", "hostname_or_ip": "10.0.0.101"}
    ).json()["id"]
    # Check sur la cible, exécuté par la sonde.
    check_id = client.post(
        "/api/checks",
        json={"host_id": target, "name": "ping cible", "type": "ping", "executor_host_id": prober},
    ).json()["id"]

    # La sonde récupère ses checks (cible = IP de l'hôte cible).
    assigned = client.get("/api/agent/checks", params={"host_id": prober}).json()
    mine = [c for c in assigned if c["id"] == check_id]
    assert len(mine) == 1
    assert mine[0]["target"] == "10.0.0.101"
    assert mine[0]["type"] == "ping"

    # La sonde pousse un résultat.
    assert client.post(
        f"/api/agent/checks/{check_id}/result",
        json={"status": "OK", "message": "reachable", "duration_ms": 12},
    ).status_code == 200

    # Le statut du check est mis à jour.
    assert client.get(f"/api/checks/{check_id}").json()["last_status"] == "OK"


def test_agent_probe_only_returns_own_checks(client, db):
    # Un check central (sans executor) ne doit pas être renvoyé à un agent.
    host = client.post(
        "/api/hosts", json={"name": "central-h", "hostname_or_ip": "10.0.0.110"}
    ).json()["id"]
    client.post("/api/checks", json={"host_id": host, "name": "central ping", "type": "ping"})
    assigned = client.get("/api/agent/checks", params={"host_id": host}).json()
    assert assigned == []
