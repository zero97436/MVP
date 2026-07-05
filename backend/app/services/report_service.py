"""Rapports : SLA (disponibilité) par hôte et MTTR (temps moyen de résolution)."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.check import Check
from app.models.check_result import CheckResult
from app.models.host import Host


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def sla(self, days: int = 30) -> dict:
        """Disponibilité (% de résultats OK) par hôte sur la période."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        ok_expr = func.sum(case((CheckResult.status == "OK", 1), else_=0))
        rows = self.db.execute(
            select(Check.host_id, func.count(CheckResult.id), ok_expr)
            .join(Check, Check.id == CheckResult.check_id)
            .where(CheckResult.checked_at >= cutoff)
            .group_by(Check.host_id)
        ).all()

        names = {h.id: h.name for h in self.db.scalars(select(Host))}
        per_host, tot_total, tot_ok = [], 0, 0
        for host_id, total, ok in rows:
            ok = ok or 0
            tot_total += total
            tot_ok += ok
            per_host.append({
                "host_id": host_id,
                "host_name": names.get(host_id, f"#{host_id}"),
                "samples": total,
                "availability": round(ok / total * 100, 3) if total else 100.0,
            })
        per_host.sort(key=lambda h: h["availability"])
        global_av = round(tot_ok / tot_total * 100, 3) if tot_total else 100.0
        return {"days": days, "global_availability": global_av, "hosts": per_host}

    def mttr(self, days: int = 30) -> dict:
        """Temps moyen de résolution des incidents + compteurs sur la période."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        alerts = list(self.db.scalars(select(Alert)))
        in_window = [a for a in alerts if _aware(a.created_at) >= cutoff]
        resolved = [a for a in in_window if a.resolved_at is not None]
        durations = [
            (_aware(a.resolved_at) - _aware(a.created_at)).total_seconds() for a in resolved
        ]
        active = sum(1 for a in in_window if a.is_active)
        mttr = round(sum(durations) / len(durations)) if durations else None
        longest = round(max(durations)) if durations else None
        return {
            "days": days,
            "incidents": len(in_window),
            "resolved": len(resolved),
            "active": active,
            "mttr_seconds": mttr,
            "longest_seconds": longest,
        }

    def pdf(self, days: int = 30) -> bytes:
        """Génère un rapport PDF (SLA par hôte + MTTR) via reportlab."""
        import io
        from datetime import datetime

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        sla = self.sla(days)
        mttr = self.mttr(days)
        styles = getSampleStyleSheet()

        def dur(sec):
            if sec is None:
                return "—"
            if sec < 60:
                return f"{round(sec)} s"
            if sec < 3600:
                return f"{round(sec / 60)} min"
            return f"{round(sec / 3600, 1)} h"

        el = [
            Paragraph("Opsora — Rapport de disponibilité", styles["Title"]),
            Paragraph(
                f"Période : {days} jours · généré le {datetime.now():%d/%m/%Y %H:%M}",
                styles["Normal"],
            ),
            Spacer(1, 0.6 * cm),
            Paragraph(f"<b>Disponibilité globale :</b> {sla['global_availability']:.2f} %", styles["Normal"]),
            Paragraph(
                f"<b>MTTR :</b> {dur(mttr['mttr_seconds'])} · "
                f"<b>Incidents :</b> {mttr['incidents']} "
                f"(actifs {mttr['active']}, résolus {mttr['resolved']}) · "
                f"<b>Plus long :</b> {dur(mttr['longest_seconds'])}",
                styles["Normal"],
            ),
            Spacer(1, 0.6 * cm),
            Paragraph("SLA par hôte", styles["Heading2"]),
        ]

        rows = [["Hôte", "Disponibilité", "Échantillons"]]
        for h in sla["hosts"]:
            rows.append([h["host_name"], f"{h['availability']:.2f} %", str(h["samples"])])
        if len(rows) == 1:
            rows.append(["(aucune donnée)", "—", "—"])

        table = Table(rows, colWidths=[9 * cm, 4 * cm, 4 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        el.append(table)

        buf = io.BytesIO()
        SimpleDocTemplate(buf, pagesize=A4, title="Rapport Opsora").build(el)
        return buf.getvalue()
