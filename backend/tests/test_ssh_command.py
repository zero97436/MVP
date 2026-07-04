from app.checks.base import CheckContext
from app.checks.registry import get_check


def _ctx(config, timeout=2):
    return CheckContext(
        hostname_or_ip="10.255.255.30", timeout_seconds=timeout,
        warning_threshold=None, critical_threshold=None, config=config,
    )


def test_ssh_command_registered():
    assert get_check("ssh_command") is not None


def test_missing_command_is_unknown():
    res = get_check("ssh_command").execute(_ctx({}))
    assert res.status.value == "UNKNOWN"


def test_unreachable_is_critical():
    res = get_check("ssh_command").execute(_ctx({"command": "uptime", "user": "x", "password": "y"}))
    assert res.status.value == "CRITICAL"
