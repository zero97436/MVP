from app.checks.base import CheckContext
from app.checks.plugins.kubernetes import KubernetesCheck
from app.checks.plugins.proxmox import ProxmoxCheck


def _ctx(config, warn=None, crit=None):
    return CheckContext(hostname_or_ip="x", timeout_seconds=5,
                        warning_threshold=warn, critical_threshold=crit, config=config)


K8S_BASE = {"api_url": "https://k8s:6443", "token": "tok"}
PVE_BASE = {"api_url": "https://pve:8006", "token_id": "sup@pve!mon", "token_secret": "s"}


def _node(name, ready="True"):
    return {"metadata": {"name": name},
            "status": {"conditions": [{"type": "Ready", "status": ready}]}}


def test_k8s_nodes(monkeypatch):
    monkeypatch.setattr("app.checks.plugins.kubernetes._fetch_json",
                        lambda *a, **k: {"items": [_node("n1"), _node("n2")]})
    res = KubernetesCheck().run(_ctx({**K8S_BASE, "mode": "nodes"}))
    assert res.status.value == "OK" and "2 node(s) Ready" in res.message

    monkeypatch.setattr("app.checks.plugins.kubernetes._fetch_json",
                        lambda *a, **k: {"items": [_node("n1"), _node("n2", ready="False")]})
    res = KubernetesCheck().run(_ctx({**K8S_BASE, "mode": "nodes"}))
    assert res.status.value == "CRITICAL" and "n2" in res.message


def test_k8s_pods(monkeypatch):
    pods = {"items": [
        {"metadata": {"name": "web-1"}, "status": {"phase": "Running", "containerStatuses": []}},
        {"metadata": {"name": "job-x"}, "status": {"phase": "Running", "containerStatuses": [
            {"state": {"waiting": {"reason": "CrashLoopBackOff"}}}]}},
    ]}
    monkeypatch.setattr("app.checks.plugins.kubernetes._fetch_json", lambda *a, **k: pods)
    res = KubernetesCheck().run(_ctx({**K8S_BASE, "mode": "pods", "namespace": "prod"}))
    assert res.status.value == "CRITICAL" and "job-x" in res.message


def test_k8s_deployment(monkeypatch):
    dep = {"metadata": {"name": "api"}, "spec": {"replicas": 3}, "status": {"readyReplicas": 2}}
    monkeypatch.setattr("app.checks.plugins.kubernetes._fetch_json", lambda *a, **k: dep)
    res = KubernetesCheck().run(_ctx({**K8S_BASE, "mode": "deployment", "name": "api"}))
    assert res.status.value == "WARNING" and "2/3" in res.message


def test_k8s_config_missing():
    assert KubernetesCheck().run(_ctx({})).status.value == "UNKNOWN"


def test_proxmox_cluster(monkeypatch):
    monkeypatch.setattr("app.checks.plugins.proxmox._fetch_json",
                        lambda *a, **k: {"data": [{"node": "pve1", "status": "online"},
                                                  {"node": "pve2", "status": "offline"}]})
    res = ProxmoxCheck().run(_ctx({**PVE_BASE}))
    assert res.status.value == "CRITICAL" and "pve2" in res.message


def test_proxmox_vms(monkeypatch):
    def fake(url, *a, **k):
        if "/qemu" in url:
            return {"data": [{"vmid": 100, "name": "web", "status": "running"},
                             {"vmid": 101, "name": "old", "status": "stopped"},
                             {"vmid": 900, "name": "tpl", "status": "stopped", "template": 1}]}
        return {"data": []}
    monkeypatch.setattr("app.checks.plugins.proxmox._fetch_json", fake)
    res = ProxmoxCheck().run(_ctx({**PVE_BASE, "mode": "vms", "node": "pve1"}))
    assert res.status.value == "CRITICAL"
    assert "old" in res.message and "tpl" not in res.message  # templates ignorés


def test_proxmox_vm_cpu_threshold(monkeypatch):
    st = {"data": {"name": "db", "vmid": 100, "status": "running",
                   "cpu": 0.87, "mem": 900, "maxmem": 1000, "uptime": 3600}}
    monkeypatch.setattr("app.checks.plugins.proxmox._fetch_json", lambda *a, **k: st)
    res = ProxmoxCheck().run(_ctx({**PVE_BASE, "mode": "vm", "node": "pve1", "vmid": 100}, warn=80, crit=95))
    assert res.status.value == "WARNING" and res.value == 87.0

    st["data"]["status"] = "stopped"
    res = ProxmoxCheck().run(_ctx({**PVE_BASE, "mode": "vm", "node": "pve1", "vmid": 100}))
    assert res.status.value == "CRITICAL"
