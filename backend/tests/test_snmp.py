from app.checks.base import CheckContext
from app.checks.plugins.snmp import SnmpCheck


def test_snmp_requires_oid_or_metric():
    ctx = CheckContext(
        hostname_or_ip="10.0.0.200", timeout_seconds=1,
        warning_threshold=None, critical_threshold=None, config={},
    )
    res = SnmpCheck().run(ctx)
    assert res.status.value == "UNKNOWN"


def test_snmp_metric_shortcut_resolves_oid():
    # Métrique 'cpu' -> un OID est résolu (le run réel échouera faute d'équipement,
    # mais on vérifie que la config est acceptée et non 'UNKNOWN config').
    ctx = CheckContext(
        hostname_or_ip="10.255.255.1", timeout_seconds=1,
        warning_threshold=80, critical_threshold=90, config={"metric": "cpu"},
    )
    res = SnmpCheck().run(ctx)
    # Hôte injoignable -> CRITICAL (timeout/erreur), surtout pas "préciser oid".
    assert res.status.value in ("CRITICAL", "UNKNOWN")
    assert "Préciser" not in (res.message or "")


def test_snmp_check_via_api(client):
    host_id = client.post(
        "/api/hosts", json={"name": "mikrotik", "hostname_or_ip": "10.255.255.2"}
    ).json()["id"]
    resp = client.post(
        "/api/checks",
        json={
            "host_id": host_id, "name": "CPU SNMP", "type": "snmp",
            "timeout_seconds": 1, "warning_threshold": 80, "critical_threshold": 90,
            "config_json": {"metric": "cpu", "community": "public"},
        },
    )
    assert resp.status_code == 201
    assert resp.json()["type"] == "snmp"
