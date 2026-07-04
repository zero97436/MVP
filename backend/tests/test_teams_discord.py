def test_create_teams_and_discord_channels(client):
    teams = client.post("/api/settings/notification-channels", json={
        "name": "teams-ops", "type": "teams",
        "config_json": {"webhook_url": "https://outlook.office.com/webhook/x"},
    })
    assert teams.status_code == 201 and teams.json()["type"] == "teams"

    disc = client.post("/api/settings/notification-channels", json={
        "name": "discord-ops", "type": "discord",
        "config_json": {"webhook_url": "https://discord.com/api/webhooks/x"},
    })
    assert disc.status_code == 201

    # Secret masqué dans la réponse de liste.
    chans = client.get("/api/settings/notification-channels").json()
    t = next(c for c in chans if c["name"] == "teams-ops")
    assert t["config_json"]["webhook_url"] == "********"


def test_teams_test_endpoint_bad_config(client):
    ch = client.post("/api/settings/notification-channels", json={
        "name": "teams-bad", "type": "teams", "config_json": {},
    }).json()
    # Pas de webhook_url -> envoi échoue proprement (pas d'appel réseau).
    assert client.post(f"/api/settings/notification-channels/{ch['id']}/test").status_code == 502
