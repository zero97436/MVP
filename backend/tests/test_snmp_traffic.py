from datetime import datetime, timedelta, timezone

from app.checks.base import CheckContext
from app.checks.registry import get_check
from app.models.check_result import CheckResult


def _ctx(db=None, check_id=None, config=None):
    return CheckContext(
        hostname_or_ip="10.255.255.50", timeout_seconds=1,
        warning_threshold=None, critical_threshold=None,
        config=config or {}, db=db, check_id=check_id,
    )


def test_registered():
    assert get_check("snmp_traffic") is not None


def test_missing_ifindex_unknown():
    assert get_check("snmp_traffic").execute(_ctx(config={})).status.value == "UNKNOWN"


def test_unreachable_critical():
    res = get_check("snmp_traffic").execute(_ctx(config={"ifindex": 1}))
    assert res.status.value == "CRITICAL"


def test_previous_reading_lookup(client, db):
    # Vérifie la récupération du relevé précédent (compteurs) depuis le dernier résultat.
    host_id = client.post("/api/hosts", json={"name": "sw", "hostname_or_ip": "10.255.255.51"}).json()["id"]
    check_id = client.post("/api/checks", json={"host_id": host_id, "name": "if1", "type": "snmp_traffic",
                                                "config_json": {"ifindex": 1}}).json()["id"]
    db.add(CheckResult(check_id=check_id, status="OK",
                       perfdata={"in_octets": 1000, "out_octets": 2000},
                       checked_at=datetime.now(timezone.utc) - timedelta(seconds=60)))
    db.commit()
    prev = get_check("snmp_traffic")._previous(_ctx(db=db, check_id=check_id, config={"ifindex": 1}))
    assert prev["in"] == 1000 and prev["out"] == 2000
