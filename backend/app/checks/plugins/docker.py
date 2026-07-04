"""Check `docker` : état d'un conteneur (ou de la flotte) via l'API Docker Engine.

config_json :
  - container : nom (ou préfixe d'id) du conteneur à surveiller.
                Absent -> mode global : tous les conteneurs doivent tourner.
  - cpu / mem : seuils optionnels (%) sur le conteneur ciblé — sinon les seuils
                warning/critical du check s'appliquent au CPU si définis.

Statuts :
  - CRITICAL : conteneur absent, exited/dead, ou unhealthy
  - WARNING  : restarting/paused, health starting, ou seuil CPU/RAM warning
  - OK       : running (healthy)
"""
from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus


class DockerCheck(BaseCheck):
    type = "docker"

    def run(self, ctx: CheckContext) -> CheckResultData:
        from app.services.docker_service import DockerUnavailable, list_containers

        target = ctx.config.get("container")
        try:
            containers = list_containers(with_stats=bool(target))
        except DockerUnavailable as exc:
            return CheckResultData(status=CheckStatus.UNKNOWN, message=str(exc))

        if not target:
            return self._fleet(containers)

        ct = next(
            (c for c in containers if c["name"] == target or c["id"].startswith(target)),
            None,
        )
        if ct is None:
            return CheckResultData(
                status=CheckStatus.CRITICAL,
                message=f"Conteneur '{target}' introuvable",
            )

        state, health = ct["state"], ct["health"]
        perf = {"state": state, "health": health, "cpu_percent": ct["cpu_percent"],
                "mem_percent": ct["mem_percent"], "mem_usage_mb": ct["mem_usage_mb"]}

        if state in ("exited", "dead") or health == "unhealthy":
            return CheckResultData(
                status=CheckStatus.CRITICAL, perfdata=perf,
                message=f"{ct['name']} : {ct['status'] or state}",
            )
        if state in ("restarting", "paused") or health == "starting":
            return CheckResultData(
                status=CheckStatus.WARNING, perfdata=perf,
                message=f"{ct['name']} : {ct['status'] or state}",
            )

        # Running : seuils CPU optionnels (warning/critical du check).
        cpu = ct["cpu_percent"]
        warn, crit = ctx.warning_threshold, ctx.critical_threshold
        if cpu is not None and crit is not None and cpu >= crit:
            status = CheckStatus.CRITICAL
        elif cpu is not None and warn is not None and cpu >= warn:
            status = CheckStatus.WARNING
        else:
            status = CheckStatus.OK
        extra = f" — CPU {cpu}%" if cpu is not None else ""
        if ct["mem_usage_mb"] is not None:
            extra += f", RAM {ct['mem_usage_mb']} Mo"
        return CheckResultData(
            status=status, value=cpu, perfdata=perf,
            message=f"{ct['name']} : {ct['status'] or 'running'}{extra}",
        )

    def _fleet(self, containers: list[dict]) -> CheckResultData:
        total = len(containers)
        down = [c["name"] for c in containers if c["state"] in ("exited", "dead")]
        flaky = [c["name"] for c in containers if c["state"] in ("restarting", "paused") or c["health"] == "unhealthy"]
        running = total - len(down) - len(flaky)
        perf = {"total": total, "running": running, "down": len(down), "flaky": len(flaky)}
        if down:
            return CheckResultData(
                status=CheckStatus.CRITICAL, value=float(running), perfdata=perf,
                message=f"{len(down)} conteneur(s) arrêté(s) : {', '.join(down[:5])} ({running}/{total} up)",
            )
        if flaky:
            return CheckResultData(
                status=CheckStatus.WARNING, value=float(running), perfdata=perf,
                message=f"{len(flaky)} conteneur(s) instable(s) : {', '.join(flaky[:5])} ({running}/{total} up)",
            )
        return CheckResultData(
            status=CheckStatus.OK, value=float(running), perfdata=perf,
            message=f"{running}/{total} conteneurs en fonctionnement",
        )
