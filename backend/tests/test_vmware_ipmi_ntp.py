from app.checks.base import CheckContext
from app.checks.plugins.ipmi import IpmiCheck
from app.checks.plugins.ntp import NtpCheck
from app.checks.plugins.vmware import VmwareCheck


def _ctx(config=None, host="10.0.0.1", warn=None, crit=None):
    return CheckContext(hostname_or_ip=host, timeout_seconds=5,
                        warning_threshold=warn, critical_threshold=crit, config=config or {})


VMW = {"api_url": "https://vc.local", "user": "ro@vsphere.local", "password": "x"}


# ---------- VMware ----------
def test_vmware_hosts(monkeypatch):
    monkeypatch.setattr("app.checks.plugins.vmware._session", lambda *a, **k: "sid")
    monkeypatch.setattr("app.checks.plugins.vmware._get", lambda *a, **k: [
        {"name": "esx1", "connection_state": "CONNECTED", "power_state": "POWERED_ON"},
        {"name": "esx2", "connection_state": "DISCONNECTED", "power_state": "POWERED_ON"},
    ])
    res = VmwareCheck().run(_ctx({**VMW, "mode": "hosts"}))
    assert res.status.value == "CRITICAL" and "esx2" in res.message

    monkeypatch.setattr("app.checks.plugins.vmware._get", lambda *a, **k: [
        {"name": "esx1", "connection_state": "CONNECTED", "power_state": "POWERED_ON"},
    ])
    assert VmwareCheck().run(_ctx({**VMW})).status.value == "OK"


def test_vmware_vm(monkeypatch):
    monkeypatch.setattr("app.checks.plugins.vmware._session", lambda *a, **k: "sid")
    monkeypatch.setattr("app.checks.plugins.vmware._get", lambda *a, **k: [
        {"name": "db01", "power_state": "POWERED_OFF"},
        {"name": "web01", "power_state": "POWERED_ON", "cpu_count": 4, "memory_size_MiB": 8192},
    ])
    assert VmwareCheck().run(_ctx({**VMW, "mode": "vm", "name": "db01"})).status.value == "CRITICAL"
    assert VmwareCheck().run(_ctx({**VMW, "mode": "vm", "name": "web01"})).status.value == "OK"
    assert VmwareCheck().run(_ctx({**VMW, "mode": "vm", "name": "fantome"})).status.value == "CRITICAL"
    # Synthèse vms.
    res = VmwareCheck().run(_ctx({**VMW, "mode": "vms"}))
    assert res.status.value == "OK" and "1/2" in res.message


def test_vmware_config_missing():
    assert VmwareCheck().run(_ctx({})).status.value == "UNKNOWN"


# ---------- IPMI / Redfish ----------
IPMI = {"api_url": "https://idrac.local", "user": "monitor", "password": "x"}


def _redfish(health="OK", power="On"):
    def fake(url, *a, **k):
        if url.endswith("/redfish/v1/Systems"):
            return {"Members": [{"@odata.id": "/redfish/v1/Systems/1"}]}
        return {"Id": "1", "Model": "PowerEdge R740", "PowerState": power, "Status": {"Health": health}}
    return fake


def test_ipmi_health(monkeypatch):
    monkeypatch.setattr("app.checks.plugins.ipmi._get", _redfish("OK", "On"))
    res = IpmiCheck().run(_ctx(IPMI))
    assert res.status.value == "OK" and "PowerEdge" in res.message

    monkeypatch.setattr("app.checks.plugins.ipmi._get", _redfish("Warning", "On"))
    assert IpmiCheck().run(_ctx(IPMI)).status.value == "WARNING"

    monkeypatch.setattr("app.checks.plugins.ipmi._get", _redfish("Critical", "On"))
    assert IpmiCheck().run(_ctx(IPMI)).status.value == "CRITICAL"


def test_ipmi_power_off(monkeypatch):
    monkeypatch.setattr("app.checks.plugins.ipmi._get", _redfish("OK", "Off"))
    assert IpmiCheck().run(_ctx(IPMI)).status.value == "CRITICAL"
    # check_power désactivé -> serveur éteint toléré.
    assert IpmiCheck().run(_ctx({**IPMI, "check_power": False})).status.value == "OK"


# ---------- NTP ----------
def test_ntp_offset_thresholds(monkeypatch):
    monkeypatch.setattr("app.checks.plugins.ntp._query_ntp", lambda *a, **k: (12.0, 8.0))
    res = NtpCheck().run(_ctx())
    assert res.status.value == "OK" and res.value == 12.0

    monkeypatch.setattr("app.checks.plugins.ntp._query_ntp", lambda *a, **k: (-250.0, 8.0))
    assert NtpCheck().run(_ctx(warn=100, crit=1000)).status.value == "WARNING"  # |−250| >= 100

    monkeypatch.setattr("app.checks.plugins.ntp._query_ntp", lambda *a, **k: (1500.0, 8.0))
    assert NtpCheck().run(_ctx()).status.value == "CRITICAL"


def test_ntp_unreachable(monkeypatch):
    def boom(*a, **k):
        raise TimeoutError("timeout")
    monkeypatch.setattr("app.checks.plugins.ntp._query_ntp", boom)
    assert NtpCheck().run(_ctx()).status.value == "CRITICAL"
