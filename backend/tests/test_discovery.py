import pytest

from app.services.discovery_service import DiscoveryService


def test_expand_cidr(db):
    svc = DiscoveryService(db)
    assert len(svc._expand("10.0.0.0/30")) == 2  # 2 hôtes utilisables
    assert svc._expand("1.2.3.4") == ["1.2.3.4"]


def test_expand_rejects_large_range(db):
    with pytest.raises(ValueError):
        DiscoveryService(db)._expand("10.0.0.0/16")


def test_suggest_maps_ports(db):
    checks = DiscoveryService(db)._suggest("192.168.1.5", [22, 80, 3306])
    types = [c["type"] for c in checks]
    assert "ping" in types and "ssh" in types and "http" in types
    assert any(c["type"] == "tcp_port" and c["config_json"]["port"] == 3306 for c in checks)


def test_import_creates_hosts_and_skips_duplicates(client):
    item = {
        "name": "srv-decouvert", "hostname_or_ip": "10.20.30.40", "environment": "decouvert",
        "checks": [{"name": "Ping", "type": "ping"}, {"name": "SSH", "type": "ssh", "config_json": {"port": 22}}],
    }
    resp = client.post("/api/discovery/import", json={"items": [item]})
    assert resp.status_code == 200
    assert resp.json()["imported"] == 1
    # Ré-import du même hôte -> ignoré.
    resp2 = client.post("/api/discovery/import", json={"items": [item]})
    assert resp2.json()["imported"] == 0
