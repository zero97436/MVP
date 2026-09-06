"""Chargement optionnel de l'édition Enterprise (séparation open-core).

Contrat : le noyau (dépôt public) ne connaît le code payant que par ce point
d'entrée. Ordre de résolution :
  1. paquet externe `orbisys_enterprise` (dépôt privé, présent uniquement dans
     l'image Enterprise) — cible finale ;
  2. bundle interne `app.enterprise_local` — transitoire, Phase 1a, en attendant
     l'extraction (Phase 1b) ;
  3. aucun des deux → édition Community, rien ne casse.

Après la Phase 1b, il suffira de supprimer `app.enterprise_local` du dépôt public :
une installation Community n'aura alors plus AUCUN code payant, et ce chargeur
retournera proprement `False`.
"""
from __future__ import annotations

import importlib

from fastapi import FastAPI

from app.core.logging import get_logger

logger = get_logger(__name__)

ENTERPRISE_PACKAGE = "orbisys_enterprise"
_LOCAL_BUNDLE = "app.enterprise_local"


def load_enterprise(app: FastAPI, api_prefix: str) -> bool:
    """Charge les modules payants s'ils sont présents. Retourne True si chargés."""
    for name, source in ((ENTERPRISE_PACKAGE, "paquet externe"), (_LOCAL_BUNDLE, "bundle interne (Phase 1a)")):
        try:
            module = importlib.import_module(name)
        except ModuleNotFoundError:
            continue
        module.install(app, api_prefix)
        logger.info("Édition Enterprise : modules chargés (%s).", source)
        return True
    logger.info("Édition Community : aucun module Enterprise présent.")
    return False
