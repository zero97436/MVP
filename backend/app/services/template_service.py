"""Modèles de checks : jeux de checks standards applicables à un hôte en un clic."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.checks.registry import CHECK_REGISTRY
from app.models.check import Check
from app.models.check_template import CheckTemplate

# Modèles fournis d'origine (créés en base au premier accès si la table est vide).
DEFAULT_TEMPLATES = [
    {
        "name": "Équipement réseau (basique)",
        "description": "Ping — pour switch, routeur, borne, imprimante…",
        "items": [
            {"name": "Ping", "type": "ping", "config_json": {}, "interval_seconds": 60},
        ],
    },
    {
        "name": "Serveur Linux",
        "description": "Ping + port SSH.",
        "items": [
            {"name": "Ping", "type": "ping", "config_json": {}, "interval_seconds": 60},
            {"name": "SSH (22)", "type": "tcp_port", "config_json": {"port": 22}, "interval_seconds": 120},
        ],
    },
    {
        "name": "Serveur Web (HTTPS)",
        "description": "Ping + HTTPS + expiration du certificat SSL.",
        "items": [
            {"name": "Ping", "type": "ping", "config_json": {}, "interval_seconds": 60},
            {"name": "HTTPS (443)", "type": "tcp_port", "config_json": {"port": 443}, "interval_seconds": 120},
            {"name": "Page web", "type": "http", "config_json": {"scheme": "https"}, "interval_seconds": 120},
            {"name": "Certificat SSL", "type": "ssl_expiry", "config_json": {},
             "interval_seconds": 3600, "warning_threshold": 30, "critical_threshold": 7},
        ],
    },
    {
        "name": "Windows (agent)",
        "description": "Seuils CPU/RAM/Disque sur les métriques poussées par l'agent.",
        "items": [
            {"name": "CPU", "type": "metric", "config_json": {"metric": "cpu_percent"},
             "interval_seconds": 120, "warning_threshold": 80, "critical_threshold": 95},
            {"name": "RAM", "type": "metric", "config_json": {"metric": "mem_percent"},
             "interval_seconds": 120, "warning_threshold": 85, "critical_threshold": 95},
            {"name": "Disque", "type": "metric", "config_json": {"metric": "disk_percent"},
             "interval_seconds": 300, "warning_threshold": 80, "critical_threshold": 90},
        ],
    },
]

TEMPLATE_ITEM_FIELDS = {
    "name", "type", "config_json", "interval_seconds", "timeout_seconds",
    "warning_threshold", "critical_threshold",
}


def _clean_items(items: list[dict]) -> list[dict]:
    """Filtre/valide les items d'un template (types connus uniquement)."""
    out = []
    for it in items:
        if not isinstance(it, dict) or not it.get("name") or it.get("type") not in CHECK_REGISTRY:
            continue
        out.append({k: v for k, v in it.items() if k in TEMPLATE_ITEM_FIELDS})
    return out


class TemplateService:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[CheckTemplate]:
        templates = list(self.db.scalars(select(CheckTemplate).order_by(CheckTemplate.name)))
        if not templates:
            # Lazy seed : crée les modèles par défaut au premier accès.
            for t in DEFAULT_TEMPLATES:
                self.db.add(CheckTemplate(**t))
            self.db.commit()
            templates = list(self.db.scalars(select(CheckTemplate).order_by(CheckTemplate.name)))
        return templates

    def create(self, name: str, items: list[dict], description: str | None = None) -> CheckTemplate | None:
        items = _clean_items(items)
        if not items:
            return None
        if self.db.scalar(select(CheckTemplate).where(CheckTemplate.name == name)):
            return None  # nom déjà pris
        tpl = CheckTemplate(name=name[:255], description=description, items=items)
        self.db.add(tpl)
        self.db.commit()
        self.db.refresh(tpl)
        return tpl

    def create_from_host(self, host_id: int, name: str, description: str | None = None) -> CheckTemplate | None:
        """Capture les checks d'un hôte existant en modèle réutilisable."""
        checks = list(self.db.scalars(select(Check).where(Check.host_id == host_id)))
        if not checks:
            return None
        items = [{
            "name": c.name, "type": c.type.value if hasattr(c.type, "value") else c.type,
            "config_json": c.config_json or {},
            "interval_seconds": c.interval_seconds, "timeout_seconds": c.timeout_seconds,
            "warning_threshold": c.warning_threshold, "critical_threshold": c.critical_threshold,
        } for c in checks]
        return self.create(name, items, description)

    def delete(self, template_id: int) -> bool:
        tpl = self.db.get(CheckTemplate, template_id)
        if not tpl:
            return False
        self.db.delete(tpl)
        self.db.commit()
        return True

    def apply(self, template_id: int, host_id: int) -> dict | None:
        """Crée les checks du modèle sur l'hôte. Anti-doublon par nom de check."""
        tpl = self.db.get(CheckTemplate, template_id)
        if not tpl:
            return None
        existing = {
            c.name for c in self.db.scalars(select(Check).where(Check.host_id == host_id))
        }
        created, skipped = [], []
        for it in tpl.items:
            if it["name"] in existing:
                skipped.append(it["name"])
                continue
            self.db.add(Check(
                host_id=host_id, name=it["name"], type=it["type"],
                config_json=it.get("config_json") or {},
                interval_seconds=it.get("interval_seconds") or 60,
                timeout_seconds=it.get("timeout_seconds") or 10,
                warning_threshold=it.get("warning_threshold"),
                critical_threshold=it.get("critical_threshold"),
            ))
            created.append(it["name"])
        self.db.commit()
        return {"created": created, "skipped": skipped}
