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
    """Charge les modules payants (routers + middleware + hooks) dans l'app API."""
    try:
        module = importlib.import_module(ENTERPRISE_PACKAGE)
    except ModuleNotFoundError:
        logger.info("Édition Community : paquet Enterprise absent.")
        return False
    module.install(app, api_prefix)
    logger.info("Édition Enterprise : modules chargés.")
    return True


def load_enterprise_hooks() -> bool:
    """Enregistre uniquement les hooks Enterprise (points d'extension).

    À appeler dans les process SANS app FastAPI (worker Celery, scheduler) pour que
    la logique payante branchée par hook (ex. push ITSM auto) fonctionne aussi hors API.
    """
    try:
        module = importlib.import_module(ENTERPRISE_PACKAGE)
    except ModuleNotFoundError:
        return False
    register = getattr(module, "register_hooks", None)
    if register is not None:
        register()
        logger.info("Édition Enterprise : hooks enregistrés.")
    return True
