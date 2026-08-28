"""RBAC : rôles personnalisés avec droits de modification par section.

Rôles intégrés (inchangés) :
  - admin    : tout (modification partout)
  - operator : modification sur toutes les sections opérationnelles
  - viewer   : lecture seule (aucune modification)

Rôles personnalisés (créés par un admin) : une liste de sections où la
modification est autorisée. La lecture reste ouverte à tout utilisateur
authentifié — le contrôle porte sur les actions d'écriture (créer/modifier/
supprimer), ce qui est le besoin réel du contrôle d'accès.
"""
from __future__ import annotations

# Sections contrôlables (une action d'écriture y est rattachée).
SECTIONS = [
    "hosts", "checks", "tickets", "bam", "maintenance",
    "templates", "knowledge", "notifications",
]

SECTION_LABELS = {
    "hosts": "Hôtes", "checks": "Checks", "tickets": "Tickets",
    "bam": "Services métier (BAM)", "maintenance": "Maintenances",
    "templates": "Templates de checks", "knowledge": "Base de connaissances",
    "notifications": "Canaux de notification",
}

# Chemin d'API -> section (le 1er préfixe qui matche gagne ; ordre important).
_PATH_MAP = [
    ("check-templates", "templates"),
    ("checks", "checks"),
    ("hosts", "hosts"),
    ("discovery", "hosts"),
    ("migrate", "hosts"),
    ("bam", "bam"),
    ("maintenances", "maintenance"),
    ("tickets", "tickets"),
    ("knowledge", "knowledge"),
    ("settings", "notifications"),
    ("ai", "checks"),
]

BUILTIN_ROLES = ("admin", "operator", "viewer")


def section_for_path(path: str) -> str | None:
    parts = [p for p in path.split("/") if p and p != "api"]
    if not parts:
        return None
    head = parts[0]
    for prefix, section in _PATH_MAP:
        if head == prefix:
            return section
    return None


def writable_sections(db, role_name: str) -> set[str]:
    """Sections où ce rôle peut écrire."""
    if role_name in ("admin", "operator"):
        return set(SECTIONS)
    if role_name == "viewer":
        return set()
    # Rôle personnalisé : lu depuis la base.
    from app.models.role import Role
    from sqlalchemy import select

    role = db.scalar(select(Role).where(Role.name == role_name))
    if not role:
        return set()  # rôle inconnu -> aucune écriture (sûr)
    return {s for s in (role.permissions or []) if s in SECTIONS}


def can_write(db, user, section: str | None) -> bool:
    if user.role == "admin":
        return True
    if section is None:
        # Section non identifiée : les rôles intégrés opérateurs gardent l'accès,
        # les rôles personnalisés/viewer non (comportement prudent).
        return user.role == "operator"
    return section in writable_sections(db, user.role)
