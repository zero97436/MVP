def test_create_slack_and_telegram_channels(client):
    slack = client.post(
        "/api/settings/notification-channels",
        json={"name": "slack-ops", "type": "slack", "config_json": {"webhook_url": "https://hooks.slack.com/x"}},
    )
    assert slack.status_code == 201
    assert slack.json()["type"] == "slack"

    tg = client.post(
        "/api/settings/notification-channels",
        json={"name": "tg-ops", "type": "telegram", "config_json": {"bot_token": "1:abc", "chat_id": "42"}},
    )
    assert tg.status_code == 201


def test_test_channel_fails_gracefully_on_bad_config(client):
    # Canal slack sans webhook_url -> l'envoi échoue proprement (pas d'appel réseau).
    ch = client.post(
        "/api/settings/notification-channels",
        json={"name": "slack-bad", "type": "slack", "config_json": {}},
    ).json()
    resp = client.post(f"/api/settings/notification-channels/{ch['id']}/test")
    assert resp.status_code == 502


def test_test_channel_404(client):
    assert client.post("/api/settings/notification-channels/99999/test").status_code == 404
