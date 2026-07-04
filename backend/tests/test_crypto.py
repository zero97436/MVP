import os

import pytest

from app.core.crypto import (
    REDACTION, decrypt_config, encrypt_config, encrypt_value,
    decrypt_value, merge_secret_config, redact_config,
)


def test_value_roundtrip():
    enc = encrypt_value("s3cret")
    assert enc.startswith("enc:") and enc != "s3cret"
    assert decrypt_value(enc) == "s3cret"
    assert decrypt_value("clair") == "clair"  # legacy non chiffré


def test_config_encrypt_decrypt_redact():
    cfg = {"user": "u", "password": "p@ss", "url": "http://x"}
    enc = encrypt_config(cfg)
    assert enc["password"].startswith("enc:")
    assert enc["url"] == "http://x"  # non secret, lisible
    assert decrypt_config(enc)["password"] == "p@ss"
    assert redact_config(enc)["password"] == REDACTION
    assert redact_config(enc)["url"] == "http://x"


def test_merge_preserves_redacted_secret():
    old = encrypt_config({"password": "real"})
    merged = merge_secret_config({"password": REDACTION}, old)
    assert decrypt_config(merged)["password"] == "real"  # ancien secret conservé
    merged2 = merge_secret_config({"password": "new"}, old)
    assert decrypt_config(merged2)["password"] == "new"  # remplacé


def test_check_secret_redacted_in_api(client):
    host_id = client.post("/api/hosts", json={"name": "se", "hostname_or_ip": "10.0.0.170"}).json()["id"]
    chk = client.post("/api/checks", json={
        "host_id": host_id, "name": "db", "type": "database",
        "config_json": {"engine": "postgresql", "user": "u", "password": "TopSecret"},
    }).json()
    # L'API ne renvoie jamais le mot de passe en clair.
    assert chk["config_json"]["password"] == REDACTION
    assert client.get(f"/api/checks/{chk['id']}").json()["config_json"]["password"] == REDACTION


def test_channel_secret_redacted_in_api(client):
    client.post("/api/settings/notification-channels", json={
        "name": "tg", "type": "telegram", "config_json": {"bot_token": "123:ABCDEF", "chat_id": "42"},
    })
    chans = client.get("/api/settings/notification-channels").json()
    tg = next(c for c in chans if c["name"] == "tg")
    assert tg["config_json"]["bot_token"] == REDACTION
    assert tg["config_json"]["chat_id"] == "42"  # non secret


@pytest.mark.skipif("db" not in os.environ.get("DATABASE_URL", ""), reason="Postgres stack indispo")
def test_encrypted_db_check_still_runs(client):
    host_id = client.post("/api/hosts", json={"name": "pg", "hostname_or_ip": "db"}).json()["id"]
    chk = client.post("/api/checks", json={
        "host_id": host_id, "name": "pgc", "type": "database", "timeout_seconds": 5,
        "config_json": {"engine": "postgresql", "port": 5432, "user": "supervision",
                        "password": "supervision", "dbname": "supervision"},
    }).json()
    # Le mot de passe est chiffré en base mais déchiffré à l'exécution -> OK.
    res = client.post(f"/api/checks/{chk['id']}/run").json()
    assert res["status"] == "OK"
