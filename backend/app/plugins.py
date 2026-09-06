"""Chargement optionnel de l'édition Enterprise (séparation open-core).

Le noyau (dépôt public) ne connaît le code payant que par ce point d'entrée : il
importe le paquet privé `orbisys_enterprise` s'il est installé (image Enterprise),
sinon il reste en édition Community — sans aucun code payant présent.
"""
from __future__ import annotations

import importlib

from fastapi import FastAPI

from app.core.logging import get_logger

logger = get_logger(__name__)

ENTERPRISE_PACKAGE = "orbisys_enterprise"


def load_enterprise(app: FastAPI, api_prefix: str) -> bool:
    """Charge les modules payants si le paquet est installé. Retourne True si chargés."""
    try:
        module = importlib.import_module(ENTERPRISE_PACKAGE)
    except ModuleNotFoundError:
        logger.info("Édition Community : paquet Enterprise absent.")
        return False
    module.install(app, api_prefix)
    logger.info("Édition Enterprise : modules chargés.")
    return True
