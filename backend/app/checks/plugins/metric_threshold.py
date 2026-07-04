"""Check `metric` : alerte sur les métriques poussées par l'agent.

Lit le dernier échantillon `host_metrics` de l'hôte et compare la métrique
choisie (cpu/mem/disk/net) aux seuils warning/critical du check.

config_json :
  - metric        : "cpu_percent" | "mem_percent" | "disk_percent" | "net_mbps" (défaut cpu_percent)
  - max_age_seconds : âge max d'un échantillon avant UNKNOWN (défaut 600)
"""
from datetime import datetime, timezone

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus

FIELDS = {"cpu_percent", "mem_percent", "disk_percent", "net_mbps",
          "process_count", "load1", "temperature"}
LABEL = {
    "cpu_percent": "CPU",
    "mem_percent": "RAM",
    "disk_percent": "Disque",
    "net_mbps": "Réseau",
    "process_count": "Processus",
    "load1": "Charge système",
    "temperature": "Température",
}


class MetricThresholdCheck(BaseCheck):
    type = "metric"

    def run(self, ctx: CheckContext) -> CheckResultData:
        field = ctx.config.get("metric", "cpu_percent")
        if field not in FIELDS:
            return CheckResultData(
                status=CheckStatus.UNKNOWN,
                message=f"Unknown metric '{field}' (expected one of {sorted(FIELDS)})",
            )
        if ctx.db is None or ctx.host_id is None:
            return CheckResultData(status=CheckStatus.UNKNOWN, message="No metric context")

        # Import local pour éviter toute dépendance circulaire au chargement.
        from app.repositories.metric_repo import MetricRepository

        metric = MetricRepository(ctx.db).latest(ctx.host_id)
        if metric is None:
            return CheckResultData(
                status=CheckStatus.UNKNOWN,
                message="Aucune métrique reçue (agent non démarré ?)",
            )

        value = getattr(metric, field, None)
        if value is None:
            return CheckResultData(
                status=CheckStatus.UNKNOWN,
                message=f"Métrique '{field}' absente du dernier échantillon",
            )

        # Fraîcheur de l'échantillon.
        max_age = int(ctx.config.get("max_age_seconds", 600))
        collected = metric.collected_at
        if collected.tzinfo is None:
            collected = collected.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - collected).total_seconds()
        if age > max_age:
            return CheckResultData(
                status=CheckStatus.UNKNOWN,
                value=float(value),
                message=f"Dernière métrique trop ancienne ({int(age)}s > {max_age}s)",
                perfdata={"metric": field, "value": value, "age_seconds": int(age)},
            )

        warn = ctx.warning_threshold if ctx.warning_threshold is not None else 80
        crit = ctx.critical_threshold if ctx.critical_threshold is not None else 90
        label = LABEL.get(field, field)
        unit = "%" if field.endswith("percent") else ""

        if value >= crit:
            status = CheckStatus.CRITICAL
        elif value >= warn:
            status = CheckStatus.WARNING
        else:
            status = CheckStatus.OK

        return CheckResultData(
            status=status,
            value=float(value),
            message=f"{label} à {value}{unit} (warn {warn}{unit} / crit {crit}{unit})",
            perfdata={"metric": field, "value": value, "warn": warn, "crit": crit},
        )
