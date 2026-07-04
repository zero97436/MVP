from app.checks.base import CheckContext
from app.checks.registry import get_check


def _ctx(config=None):
    return CheckContext(
        hostname_or_ip="10.255.255.40", timeout_seconds=1,
        warning_threshold=None, critical_threshold=None, config=config or {},
    )


def test_new_types_registered():
    for t in ("imap", "pop3", "ldap"):
        assert get_check(t) is not None


def test_imap_unreachable_critical():
    assert get_check("imap").execute(_ctx()).status.value == "CRITICAL"


def test_pop3_unreachable_critical():
    assert get_check("pop3").execute(_ctx()).status.value == "CRITICAL"


def test_ldap_unreachable_critical():
    assert get_check("ldap").execute(_ctx()).status.value == "CRITICAL"


def test_create_imap_check_via_api(client):
    host_id = client.post("/api/hosts", json={"name": "mail", "hostname_or_ip": "10.255.255.41"}).json()["id"]
    resp = client.post("/api/checks", json={
        "host_id": host_id, "name": "IMAP", "type": "imap", "timeout_seconds": 1,
        "config_json": {"port": 143},
    })
    assert resp.status_code == 201
