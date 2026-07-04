from app.checks.base import CheckContext
from app.checks.plugins.docker import DockerCheck


def _ct(name, state="running", status="Up 2 hours", health=None, cpu=None, mem=None):
    return {"id": "abc123456789", "name": name, "image": "img", "state": state,
            "status": status, "health": health, "cpu_percent": cpu,
            "mem_percent": mem, "mem_usage_mb": 100.0 if cpu is not None else None}


def _ctx(config, warn=None, crit=None):
    return CheckContext(hostname_or_ip="localhost", timeout_seconds=5,
                        warning_threshold=warn, critical_threshold=crit, config=config)


def test_docker_container_running_ok(monkeypatch):
    monkeypatch.setattr("app.services.docker_service.list_containers",
                        lambda with_stats=False: [_ct("web", cpu=12.0)])
    res = DockerCheck().run(_ctx({"container": "web"}))
    assert res.status.value == "OK"
    assert "CPU 12.0%" in res.message


def test_docker_container_exited_critical(monkeypatch):
    monkeypatch.setattr("app.services.docker_service.list_containers",
                        lambda with_stats=False: [_ct("db", state="exited", status="Exited (1) 5 min ago")])
    res = DockerCheck().run(_ctx({"container": "db"}))
    assert res.status.value == "CRITICAL"


def test_docker_container_unhealthy_and_missing(monkeypatch):
    monkeypatch.setattr("app.services.docker_service.list_containers",
                        lambda with_stats=False: [_ct("api", status="Up 1 hour (unhealthy)", health="unhealthy")])
    assert DockerCheck().run(_ctx({"container": "api"})).status.value == "CRITICAL"
    assert DockerCheck().run(_ctx({"container": "fantome"})).status.value == "CRITICAL"


def test_docker_cpu_thresholds(monkeypatch):
    monkeypatch.setattr("app.services.docker_service.list_containers",
                        lambda with_stats=False: [_ct("worker", cpu=85.0)])
    res = DockerCheck().run(_ctx({"container": "worker"}, warn=80, crit=95))
    assert res.status.value == "WARNING"


def test_docker_fleet_mode(monkeypatch):
    monkeypatch.setattr("app.services.docker_service.list_containers",
                        lambda with_stats=False: [
                            _ct("a"), _ct("b"), _ct("c", state="exited", status="Exited (137)"),
                        ])
    res = DockerCheck().run(_ctx({}))
    assert res.status.value == "CRITICAL"
    assert "c" in res.message

    monkeypatch.setattr("app.services.docker_service.list_containers",
                        lambda with_stats=False: [_ct("a"), _ct("b")])
    res = DockerCheck().run(_ctx({}))
    assert res.status.value == "OK"
    assert res.value == 2.0


def test_docker_route_available(client, monkeypatch):
    monkeypatch.setattr("app.services.docker_service.list_containers",
                        lambda with_stats=False: [_ct("web")])
    data = client.get("/api/docker/containers").json()
    assert data["available"] is True
    assert data["containers"][0]["name"] == "web"
