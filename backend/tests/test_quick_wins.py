from app.checks.base import CheckContext
from app.checks.registry import get_check


def test_windows_service_registered_and_central_unknown():
    chk = get_check("windows_service")
    assert chk is not None
    ctx = CheckContext(
        hostname_or_ip="10.0.0.1", timeout_seconds=1,
        warning_threshold=None, critical_threshold=None, config={"service": "Spooler"},
    )
    # Exécution centrale -> UNKNOWN (doit passer par l'agent).
    assert chk.run(ctx).status.value == "UNKNOWN"


def test_sms_channel_secret_redacted(client):
    ch = client.post("/api/settings/notification-channels", json={
        "name": "sms-astreinte", "type": "sms",
        "config_json": {"account_sid": "AC1", "auth_token": "TOK", "from": "+1", "to": "+2"},
    })
    assert ch.status_code == 201
    chans = client.get("/api/settings/notification-channels").json()
    sms = next(c for c in chans if c["name"] == "sms-astreinte")
    assert sms["config_json"]["auth_token"] == "********"  # secret masqué
    assert sms["config_json"]["from"] == "+1"               # non secret


def test_script_channel_created(client):
    ch = client.post("/api/settings/notification-channels", json={
        "name": "handler", "type": "script", "config_json": {"command": "echo hello"},
    })
    assert ch.status_code == 201
    # Test réel : la commande 'echo' réussit -> envoi OK.
    assert client.post(f"/api/settings/notification-channels/{ch.json()['id']}/test").json()["sent"] is True
