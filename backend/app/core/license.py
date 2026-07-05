"""Licence — modèle open-core.

Édition **Community** (sans clé) : toutes les fonctionnalités de supervision,
hôtes ILLIMITÉS. Édition **Enterprise** (clé signée) : débloque les
fonctionnalités enterprise (SSO, HA, multi-tenant MSP, conformité…) et le support.

Signature asymétrique Ed25519 :
  - la clé PUBLIQUE ci-dessous vérifie les licences (sans danger dans un dépôt public) ;
  - la clé PRIVÉE reste chez l'éditeur (scripts/generate_license.py, jamais distribuée).

Format de clé : base64url(payload_json) + "." + signature_ed25519_hex
payload : {"plan": "enterprise", "customer": "...", "features": ["sso", "ha"],
           "max_hosts": null, "expires": "2027-01-01"}
  - features  : fonctionnalités enterprise débloquées (voir ENTERPRISE_FEATURES)
  - max_hosts : optionnel (null/absent = illimité) — réservé aux accords OEM
  - expires   : optionnel (absent = perpétuelle)

Une clé invalide, falsifiée ou expirée est ignorée -> retour à Community.
"""
from __future__ import annotations

import base64
import json
from datetime import date
from functools import lru_cache

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.core.config import settings

# Clé publique Ed25519 de l'éditeur (vérification uniquement).
PUBLIC_KEY_HEX = "3e3884b11f4bdded21a6b42885fd0e7944db37c2e5da7e501d75b9ec74894cfe"

# Fonctionnalités enterprise connues (les clés peuvent en activer un sous-ensemble).
ENTERPRISE_FEATURES = {"sso", "ha", "multi_tenant", "audit", "support"}

COMMUNITY_PLAN = {
    "plan": "community",
    "max_hosts": None,  # illimité
    "features": [],
    "customer": None,
    "expires": None,
}


def _verify(key: str) -> dict | None:
    try:
        payload_b64, sig_hex = key.strip().split(".")
        payload_raw = base64.urlsafe_b64decode(payload_b64 + "==")
        public = Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUBLIC_KEY_HEX))
        public.verify(bytes.fromhex(sig_hex), payload_raw)
        payload = json.loads(payload_raw)
        expires = payload.get("expires")
        if expires and date.fromisoformat(expires) < date.today():
            return None  # licence expirée
        return payload
    except Exception:  # noqa: BLE001 — clé malformée/falsifiée = Community
        return None


@lru_cache
def _cached_license(key: str) -> dict:
    payload = _verify(key) if key else None
    if not payload:
        return dict(COMMUNITY_PLAN)
    max_hosts = payload.get("max_hosts")
    if max_hosts is not None and (not isinstance(max_hosts, int) or max_hosts < 1):
        max_hosts = None
    features = [f for f in payload.get("features", []) if f in ENTERPRISE_FEATURES]
    return {
        "plan": payload.get("plan", "enterprise"),
        "max_hosts": max_hosts,
        "features": features,
        "customer": payload.get("customer"),
        "expires": payload.get("expires"),
    }


def get_license() -> dict:
    return _cached_license(settings.LICENSE_KEY or "")


def has_feature(name: str) -> bool:
    """À utiliser pour conditionner les futures fonctionnalités enterprise."""
    return name in get_license()["features"]


def max_hosts() -> int | None:
    """None = illimité."""
    return get_license()["max_hosts"]
