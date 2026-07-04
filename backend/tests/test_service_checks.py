from app.checks.base import CheckContext
from app.checks.registry import get_check


def _ctx(config=None):
    return CheckContext(
        hostname_or_ip="10.255.255.9", timeout_seconds=1,
        warning_threshold=None, critical_threshold=None, config=config or {},
    )


def test_new_check_types_registered():
    for t in ("dns", "ssh", "smtp", "ftp"):
        assert get_check(t) is not None


def test_ssh_unreachable_is_critical():
    res = get_check("ssh").execute(_ctx())
    assert res.status.value == "CRITICAL"


def test_smtp_unreachable_is_critical():
    res = get_check("smtp").execute(_ctx())
    assert res.status.value == "CRITICAL"


def test_dns_unreachable_is_critical():
    res = get_check("dns").execute(_ctx({"name": "example.com"}))
    assert res.status.value == "CRITICAL"


def test_create_dns_check_via_api(client):
    host_id = client.post(
        "/api/hosts", json={"name": "dns-srv", "hostname_or_ip": "10.255.255.10"}
    ).json()["id"]
    resp = client.post(
        "/api/checks",
        json={"host_id": host_id, "name": "Resolve", "type": "dns",
              "timeout_seconds": 1, "config_json": {"name": "example.com"}},
    )
    assert resp.status_code == 201
