"""Migration depuis d'autres outils : import CSV universel + fichiers Nagios/Icinga.

CSV attendu (en-têtes insensibles à la casse, séparateur , ou ;) :
  name, ip (ou address/hostname), environment, location, latitude, longitude,
  template (nom d'un modèle de checks à appliquer), parent (nom d'un hôte)

Nagios : parse les blocs `define host {...}` (host_name, alias, address, parents)
et `define service {...}` (check_command mappé vers nos types de checks).
"""
from __future__ import annotations

import csv
import io
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.check import Check
from app.models.check_template import CheckTemplate
from app.models.host import Host

# check_command Nagios -> (type, config) Opsora.
NAGIOS_COMMANDS: dict[str, tuple[str, dict]] = {
    "check_ping": ("ping", {}),
    "check-host-alive": ("ping", {}),
    "check_icmp": ("ping", {}),
    "check_ssh": ("tcp_port", {"port": 22}),
    "check_tcp": ("tcp_port", {}),
    "check_http": ("http", {}),
    "check_https": ("http", {"scheme": "https"}),
    "check_smtp": ("smtp", {}),
    "check_ftp": ("ftp", {}),
    "check_dns": ("dns", {}),
    "check_imap": ("imap", {}),
    "check_pop": ("pop3", {}),
    "check_ldap": ("ldap", {}),
    "check_snmp": ("snmp", {}),
}

IP_KEYS = ("ip", "address", "hostname", "hostname_or_ip", "host")


class ImportService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- CSV ----------
    def parse_csv(self, content: str) -> tuple[list[dict], list[str]]:
        warnings: list[str] = []
        # Détection du séparateur (, ou ;).
        first = content.strip().splitlines()[0] if content.strip() else ""
        delim = ";" if first.count(";") > first.count(",") else ","
        reader = csv.DictReader(io.StringIO(content), delimiter=delim)
        hosts: list[dict] = []
        for i, row in enumerate(reader, start=2):
            r = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            name = r.get("name") or r.get("nom")
            ip = next((r[k] for k in IP_KEYS if r.get(k)), None)
            if not name and not ip:
                continue
            if not ip:
                warnings.append(f"ligne {i} : pas d'IP/adresse -> ignorée")
                continue
            host = {
                "name": name or ip,
                "hostname_or_ip": ip,
                "environment": r.get("environment") or r.get("environnement") or "production",
                "location": r.get("location") or r.get("site") or None,
                "latitude": _float(r.get("latitude") or r.get("lat")),
                "longitude": _float(r.get("longitude") or r.get("lon") or r.get("lng")),
                "template": r.get("template") or None,
                "parent": r.get("parent") or None,
                "checks": [],
            }
            hosts.append(host)
        return hosts, warnings

    # ---------- Nagios ----------
    def parse_nagios(self, content: str) -> tuple[list[dict], list[str]]:
        warnings: list[str] = []
        blocks = re.findall(r"define\s+(host|service)\s*\{(.*?)\}", content, re.S)
        hosts: dict[str, dict] = {}
        services: list[dict] = []
        for kind, body in blocks:
            attrs: dict[str, str] = {}
            for line in body.splitlines():
                line = line.split(";")[0].strip()  # commentaires inline Nagios
                if not line:
                    continue
                parts = line.split(None, 1)
                if len(parts) == 2:
                    attrs[parts[0].strip()] = parts[1].strip()
            if kind == "host":
                name = attrs.get("host_name")
                if not name or not attrs.get("address"):
                    if name or attrs:
                        warnings.append(f"host '{name or '?'}' sans address -> ignoré (template ?)")
                    continue
                hosts[name] = {
                    "name": attrs.get("alias") or name,
                    "nagios_name": name,
                    "hostname_or_ip": attrs["address"],
                    "environment": "production",
                    "location": None, "latitude": None, "longitude": None,
                    "template": None,
                    "parent": (attrs.get("parents") or "").split(",")[0].strip() or None,
                    "checks": [{"name": "Ping", "type": "ping", "config_json": {}}],
                }
            else:  # service
                services.append(attrs)

        for svc in services:
            target = svc.get("host_name", "")
            desc = svc.get("service_description", "service")
            cmd_full = svc.get("check_command", "")
            cmd, *args = cmd_full.split("!")
            mapped = NAGIOS_COMMANDS.get(cmd)
            for host_name in [h.strip() for h in target.split(",") if h.strip()]:
                host = hosts.get(host_name)
                if not host:
                    continue
                if not mapped:
                    warnings.append(f"commande '{cmd}' non mappée ({desc} sur {host_name}) -> à recréer manuellement")
                    continue
                ctype, cfg = mapped
                cfg = dict(cfg)
                # check_tcp!8080 -> port en argument.
                if ctype == "tcp_port" and args and args[0].isdigit():
                    cfg["port"] = int(args[0])
                if ctype == "tcp_port" and "port" not in cfg:
                    warnings.append(f"check_tcp sans port ({desc} sur {host_name}) -> ignoré")
                    continue
                host["checks"].append({"name": desc[:255], "type": ctype, "config_json": cfg})

        return list(hosts.values()), warnings

    # ---------- application ----------
    def apply(self, hosts: list[dict]) -> dict:
        existing = {h.hostname_or_ip: h for h in self.db.scalars(select(Host))}
        by_name = {h.name: h for h in existing.values()}
        templates = {t.name: t for t in self.db.scalars(select(CheckTemplate))}
        created, skipped, checks_created = [], [], 0
        warnings: list[str] = []
        name_map: dict[str, Host] = {}

        # Passe 1 : création des hôtes.
        for h in hosts:
            if h["hostname_or_ip"] in existing:
                skipped.append(h["name"])
                name_map[h.get("nagios_name") or h["name"]] = existing[h["hostname_or_ip"]]
                continue
            host = Host(
                name=h["name"], hostname_or_ip=h["hostname_or_ip"],
                environment=h.get("environment") or "production",
                description="Importé (migration)",
                location=h.get("location"), latitude=h.get("latitude"), longitude=h.get("longitude"),
            )
            self.db.add(host)
            self.db.flush()
            name_map[h.get("nagios_name") or h["name"]] = host
            created.append(h["name"])

            # Checks directs (Nagios) — dédoublonnés par nom.
            seen: set[str] = set()
            for c in h.get("checks", []):
                if c["name"] in seen:
                    continue
                seen.add(c["name"])
                self.db.add(Check(host_id=host.id, name=c["name"], type=c["type"],
                                  config_json=c.get("config_json") or {}))
                checks_created += 1

            # Template (CSV).
            tpl_name = h.get("template")
            if tpl_name:
                tpl = templates.get(tpl_name)
                if not tpl:
                    warnings.append(f"template '{tpl_name}' introuvable pour {h['name']}")
                else:
                    for it in tpl.items:
                        if it["name"] in seen:
                            continue
                        seen.add(it["name"])
                        self.db.add(Check(
                            host_id=host.id, name=it["name"], type=it["type"],
                            config_json=it.get("config_json") or {},
                            interval_seconds=it.get("interval_seconds") or 60,
                            timeout_seconds=it.get("timeout_seconds") or 10,
                            warning_threshold=it.get("warning_threshold"),
                            critical_threshold=it.get("critical_threshold"),
                        ))
                        checks_created += 1

        # Passe 2 : résolution des parents (dépendances).
        for h in hosts:
            parent_ref = h.get("parent")
            if not parent_ref:
                continue
            child = name_map.get(h.get("nagios_name") or h["name"])
            parent = name_map.get(parent_ref) or by_name.get(parent_ref)
            if child and parent and child.id != parent.id:
                child.parent_host_id = parent.id
            elif child:
                warnings.append(f"parent '{parent_ref}' introuvable pour {h['name']}")

        self.db.commit()
        return {"created": created, "skipped": skipped,
                "checks_created": checks_created, "warnings": warnings}


def _float(v: str | None) -> float | None:
    if not v:
        return None
    try:
        return float(v.replace(",", "."))
    except ValueError:
        return None
