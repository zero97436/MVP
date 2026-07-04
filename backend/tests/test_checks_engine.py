"""Tests unitaires du moteur de checks (sans DB)."""
from app.checks.base import CheckContext
from app.checks.plugins.disk_usage import DiskUsageCheck
from app.checks.plugins.tcp_port import TcpPortCheck
from app.models.enums import CheckStatus


def _ctx(**kw):
    base = dict(
        hostname_or_ip="127.0.0.1",
        timeout_seconds=2,
        warning_threshold=80,
        critical_threshold=90,
        config={},
    )
    base.update(kw)
    return CheckContext(**base)


def test_disk_usage_unknown_without_mock():
    res = DiskUsageCheck().execute(_ctx())
    assert res.status == CheckStatus.UNKNOWN


def test_disk_usage_mock_critical():
    res = DiskUsageCheck().execute(_ctx(config={"mock": True, "mock_value": 95}))
    assert res.status == CheckStatus.CRITICAL
    assert res.value == 95


def test_tcp_port_missing_port():
    res = TcpPortCheck().execute(_ctx(config={}))
    assert res.status == CheckStatus.UNKNOWN


def test_tcp_port_closed():
    # Port très improbable -> CRITICAL
    res = TcpPortCheck().execute(_ctx(config={"port": 1}))
    assert res.status == CheckStatus.CRITICAL
