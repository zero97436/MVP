"""Check snmp_traffic : débit entrant/sortant d'une interface réseau via SNMP.

Le trafic SNMP est un COMPTEUR cumulatif : le débit se calcule par delta avec le
relevé précédent (stocké dans le perfdata du dernier résultat de ce check).

config_json :
  - ifindex   : index de l'interface (voir GET /api/snmp/interfaces)
  - community : communauté SNMP (défaut 'public')
  - version   : '1' | '2c' (défaut '2c')
  - link_speed_mbps : débit du lien (optionnel) -> alerte sur la SATURATION (%)
  - hc        : compteurs 64 bits ifHC* (défaut true ; mettre false si non supportés)

Seuils : si link_speed_mbps fourni, warning/critical = % saturation (défaut 70/90) ;
sinon, sur le débit max (Mbps).
"""
from datetime import datetime, timezone

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus


class SnmpTrafficCheck(BaseCheck):
    type = "snmp_traffic"

    def run(self, ctx: CheckContext) -> CheckResultData:
        cfg = ctx.config
        idx = cfg.get("ifindex")
        if idx is None:
            return CheckResultData(status=CheckStatus.UNKNOWN, message="'ifindex' manquant")
        community = str(cfg.get("community", "public"))
        version = str(cfg.get("version", "2c"))
        hc = bool(cfg.get("hc", True))
        in_oid = f"1.3.6.1.2.1.31.1.1.1.6.{idx}" if hc else f"1.3.6.1.2.1.2.2.1.10.{idx}"
        out_oid = f"1.3.6.1.2.1.31.1.1.1.10.{idx}" if hc else f"1.3.6.1.2.1.2.2.1.16.{idx}"
        in_err_oid = f"1.3.6.1.2.1.2.2.1.14.{idx}"   # ifInErrors
        out_err_oid = f"1.3.6.1.2.1.2.2.1.20.{idx}"  # ifOutErrors

        from app.checks.plugins._snmp import snmpget

        try:
            vals = snmpget(ctx.hostname_or_ip, community, version,
                           [in_oid, out_oid, in_err_oid, out_err_oid], ctx.timeout_seconds)
            cur_in, cur_out = int(vals[0]), int(vals[1])
            cur_ierr, cur_oerr = int(vals[2]), int(vals[3])
        except Exception as exc:  # noqa: BLE001
            return CheckResultData(status=CheckStatus.CRITICAL, message=f"SNMP trafic erreur : {str(exc)[:100]}")

        now = datetime.now(timezone.utc)
        prev = self._previous(ctx)
        perf_now = {"in_octets": cur_in, "out_octets": cur_out,
                    "in_err": cur_ierr, "out_err": cur_oerr}

        if not prev:
            return CheckResultData(
                status=CheckStatus.UNKNOWN,
                message="Première collecte (référence) — débit au prochain passage",
                perfdata=perf_now,
            )

        dt = (now - prev["at"]).total_seconds()
        din, dout = cur_in - prev["in"], cur_out - prev["out"]
        if dt <= 0 or din < 0 or dout < 0:  # redémarrage compteur / wrap
            return CheckResultData(status=CheckStatus.UNKNOWN, message="Compteur réinitialisé", perfdata=perf_now)

        in_mbps = round(din * 8 / 1_000_000 / dt, 2)
        out_mbps = round(dout * 8 / 1_000_000 / dt, 2)
        peak = max(in_mbps, out_mbps)
        # Erreurs d'interface (delta depuis le dernier relevé).
        err_delta = max(0, (cur_ierr - prev.get("ierr", cur_ierr))) + max(0, (cur_oerr - prev.get("oerr", cur_oerr)))
        perf = {**perf_now, "in_mbps": in_mbps, "out_mbps": out_mbps, "errors_delta": err_delta}

        link = cfg.get("link_speed_mbps")
        if link:
            sat = round(peak / float(link) * 100, 1)
            perf["saturation_pct"] = sat
            warn = ctx.warning_threshold if ctx.warning_threshold is not None else 70
            crit = ctx.critical_threshold if ctx.critical_threshold is not None else 90
            status = CheckStatus.CRITICAL if sat >= crit else CheckStatus.WARNING if sat >= warn else CheckStatus.OK
            msg = f"↓{in_mbps} ↑{out_mbps} Mb/s — saturation {sat}% (lien {link} Mb/s)"
            value = sat
        else:
            warn, crit = ctx.warning_threshold, ctx.critical_threshold
            status = CheckStatus.OK
            if crit is not None and peak >= crit:
                status = CheckStatus.CRITICAL
            elif warn is not None and peak >= warn:
                status = CheckStatus.WARNING
            msg = f"↓{in_mbps} ↑{out_mbps} Mb/s"
            value = peak

        # Erreurs d'interface : dégrade en WARNING si le seuil max_errors est franchi.
        max_err = cfg.get("max_errors")
        if max_err is not None and err_delta >= int(max_err) and status == CheckStatus.OK:
            status = CheckStatus.WARNING
            msg += f" — {err_delta} erreur(s) d'interface"
        elif err_delta > 0:
            msg += f" ({err_delta} err.)"

        return CheckResultData(status=status, value=value, message=msg, perfdata=perf)

    def _previous(self, ctx: CheckContext) -> dict | None:
        if ctx.db is None or ctx.check_id is None:
            return None
        from app.repositories.check_repo import CheckRepository

        results = CheckRepository(ctx.db).list_results(ctx.check_id, limit=1)
        if not results:
            return None
        r = results[0]
        pd = r.perfdata or {}
        if "in_octets" not in pd or "out_octets" not in pd:
            return None
        at = r.checked_at if r.checked_at.tzinfo else r.checked_at.replace(tzinfo=timezone.utc)
        return {
            "in": int(pd["in_octets"]), "out": int(pd["out_octets"]), "at": at,
            "ierr": int(pd.get("in_err", 0)), "oerr": int(pd.get("out_err", 0)),
        }
