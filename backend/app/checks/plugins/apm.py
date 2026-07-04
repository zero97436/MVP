"""Check `apm` : alerte sur les métriques applicatives (APM).

Agrège les échantillons APM d'une application sur une fenêtre glissante et
compare la métrique choisie aux seuils warning/critical du check.

config_json :
  - app            : nom de l'application (obligatoire)
  - metric         : "error_rate" (%) | "latency_ms" | "rpm" (défaut error_rate)
  - window_minutes : fenêtre d'agrégation (défaut 15)
  - min_rpm        : pour metric=rpm, alerte si débit EN DESSOUS des seuils
                     (app silencieuse) — sinon seuils = plafonds.
"""
from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus

METRICS = {"error_rate", "latency_ms", "rpm"}
LABEL = {"error_rate": "Taux d'erreur", "latency_ms": "Latence", "rpm": "Débit"}
UNIT = {"error_rate": "%", "latency_ms": " ms", "rpm": " req/min"}


class ApmCheck(BaseCheck):
    type = "apm"

    def run(self, ctx: CheckContext) -> CheckResultData:
        app = ctx.config.get("app")
        if not app:
            return CheckResultData(status=CheckStatus.UNKNOWN, message="config 'app' manquante")
        metric = ctx.config.get("metric", "error_rate")
        if metric not in METRICS:
            return CheckResultData(
                status=CheckStatus.UNKNOWN,
                message=f"Métrique '{metric}' inconnue (attendu {sorted(METRICS)})",
            )
        if ctx.db is None:
            return CheckResultData(status=CheckStatus.UNKNOWN, message="Pas de contexte DB")

        from app.services.apm_service import ApmService

        window = int(ctx.config.get("window_minutes", 15))
        stats = ApmService(ctx.db).window_stats(app, minutes=window)
        if stats["requests"] == 0:
            return CheckResultData(
                status=CheckStatus.UNKNOWN,
                message=f"Aucune donnée APM pour '{app}' sur {window} min",
            )

        value = stats.get(metric)
        if value is None:
            return CheckResultData(
                status=CheckStatus.UNKNOWN,
                message=f"Métrique '{metric}' absente pour '{app}'",
            )

        defaults = {"error_rate": (5, 10), "latency_ms": (500, 2000), "rpm": (10, 1)}
        warn = ctx.warning_threshold if ctx.warning_threshold is not None else defaults[metric][0]
        crit = ctx.critical_threshold if ctx.critical_threshold is not None else defaults[metric][1]

        low_is_bad = metric == "rpm" and bool(ctx.config.get("min_rpm", True))
        if low_is_bad:
            status = CheckStatus.CRITICAL if value <= crit else CheckStatus.WARNING if value <= warn else CheckStatus.OK
        else:
            status = CheckStatus.CRITICAL if value >= crit else CheckStatus.WARNING if value >= warn else CheckStatus.OK

        unit = UNIT[metric]
        return CheckResultData(
            status=status,
            value=float(value),
            message=(
                f"{app} : {LABEL[metric]} {value}{unit} sur {window} min "
                f"({stats['requests']} req, {stats['errors']} err) — warn {warn}{unit} / crit {crit}{unit}"
            ),
            perfdata={"app": app, "metric": metric, "value": value,
                      "requests": stats["requests"], "errors": stats["errors"],
                      "rpm": stats["rpm"], "latency_ms": stats["latency_ms"],
                      "error_rate": stats["error_rate"]},
        )
