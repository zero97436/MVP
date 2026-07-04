"""BAM : calcul du statut d'un service métier à partir de ses composants."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.business_service import BusinessService, BusinessServiceComponent
from app.models.check import Check

SEVERITY = {"CRITICAL": 0, "WARNING": 1, "UNKNOWN": 2, "OK": 3}


def _worst(statuses: list[str]) -> str:
    for s in ("CRITICAL", "WARNING", "UNKNOWN"):
        if s in statuses:
            return s
    return "OK"


class BamService:
    def __init__(self, db: Session):
        self.db = db

    def _component_status(self, comp: BusinessServiceComponent) -> tuple[str, str]:
        """Renvoie (statut, libellé) d'un composant (check ou hôte)."""
        if comp.check_id:
            check = self.db.get(Check, comp.check_id)
            if not check:
                return "UNKNOWN", comp.label or f"check #{comp.check_id}"
            return (check.last_status or "UNKNOWN"), (comp.label or check.name)
        if comp.host_id:
            checks = list(self.db.scalars(select(Check).where(Check.host_id == comp.host_id)))
            worst = _worst([c.last_status or "UNKNOWN" for c in checks]) if checks else "UNKNOWN"
            from app.models.host import Host

            host = self.db.get(Host, comp.host_id)
            return worst, (comp.label or (host.name if host else f"hôte #{comp.host_id}"))
        return "UNKNOWN", comp.label or "?"

    def compute(self, bs: BusinessService) -> dict:
        comps = []
        statuses = []
        for c in bs.components:
            st, label = self._component_status(c)
            statuses.append(st)
            comps.append({"id": c.id, "label": label, "status": st,
                          "check_id": c.check_id, "host_id": c.host_id})

        ok = sum(1 for s in statuses if s == "OK")
        total = len(statuses)
        if total == 0:
            status = "UNKNOWN"
        elif bs.rule == "percent":
            pct = ok / total * 100
            warn = bs.warning_threshold if bs.warning_threshold is not None else 99
            crit = bs.critical_threshold if bs.critical_threshold is not None else 90
            status = "CRITICAL" if pct < crit else "WARNING" if pct < warn else "OK"
        else:  # worst
            status = _worst(statuses)

        return {
            "id": bs.id, "name": bs.name, "description": bs.description,
            "rule": bs.rule, "status": status,
            "category": bs.category or "Général", "icon": bs.icon,
            "pos_x": bs.pos_x, "pos_y": bs.pos_y,
            "ok_count": ok, "total": total, "components": comps,
        }

    def list(self) -> list[dict]:
        services = self.db.scalars(select(BusinessService).order_by(BusinessService.name))
        result = [self.compute(bs) for bs in services]
        result.sort(key=lambda r: SEVERITY.get(r["status"], 2))
        return result

    def create(self, **data) -> BusinessService:
        bs = BusinessService(**data)
        self.db.add(bs)
        self.db.commit()
        self.db.refresh(bs)
        return bs

    def update(self, bs_id: int, **fields) -> BusinessService | None:
        bs = self.db.get(BusinessService, bs_id)
        if not bs:
            return None
        for key, value in fields.items():
            if value is not None and hasattr(bs, key):
                setattr(bs, key, value)
        self.db.commit()
        self.db.refresh(bs)
        return bs

    def set_positions(self, positions: list[dict]) -> int:
        """Applique une liste de {id, pos_x, pos_y}. Renvoie le nombre mis à jour."""
        updated = 0
        for p in positions:
            bs = self.db.get(BusinessService, p["id"])
            if bs:
                bs.pos_x = p.get("pos_x")
                bs.pos_y = p.get("pos_y")
                updated += 1
        self.db.commit()
        return updated

    def delete(self, bs_id: int) -> bool:
        bs = self.db.get(BusinessService, bs_id)
        if not bs:
            return False
        self.db.delete(bs)
        self.db.commit()
        return True

    def add_component(self, bs_id: int, **data) -> BusinessServiceComponent | None:
        if not self.db.get(BusinessService, bs_id):
            return None
        comp = BusinessServiceComponent(business_service_id=bs_id, **data)
        self.db.add(comp)
        self.db.commit()
        self.db.refresh(comp)
        return comp

    def remove_component(self, comp_id: int) -> bool:
        comp = self.db.get(BusinessServiceComponent, comp_id)
        if not comp:
            return False
        self.db.delete(comp)
        self.db.commit()
        return True
