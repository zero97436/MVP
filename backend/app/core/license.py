"""Licence : version gratuite limitée à 100 hôtes, déblocable par clé signée.

Signature asymétrique Ed25519 :
  - la clé PUBLIQUE ci-dessous vérifie les licences (sans danger dans un dépôt public) ;
  - la clé PRIVÉE reste chez l'éditeur (scripts/generate_license.py, jamais distribuée) —
    elle seule permet de générer des clés valides.

Format de clé : base64url(payload_json) + "." + signature_ed25519_hex
payload : {"plan": "pro", "max_hosts": 1000, "customer": "...", "expires": "2027-01-01"}

Une clé invalide, falsifiée ou expirée est ignorée -> retour au plan free.

⚠️ Logiciel auto-hébergé et open source : ceci est une barrière commerciale honnête,
   pas du DRM incassable (l'utilisateur peut patcher le code). Même modèle que GitLab CE/EE.
"""
from __future__ import annotations

import base64
import json
from datetime import date
from functools import lru_cache

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.core.config import settings

# Clé publique Ed25519 de l'éditeur (vérification uniquement — impossible de
# générer une licence avec ; il faut la clé privée correspondante).
PUBLIC_KEY_HEX = "3e3884b11f4bdded21a6b42885fd0e7944db37c2e5da7e501d75b9ec74894cfe"

FREE_PLAN = {"plan": "free", "max_hosts": 100, "customer": None, "expires": None}


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
        if not isinstance(payload.get("max_hosts"), int) or payload["max_hosts"] < 1:
            return None
        return payload
    except (InvalidSignature, Exception):  # noqa: BLE001 — clé malformée = plan free
        return None


@lru_cache
def _cached_license(key: str) -> dict:
    payload = _verify(key) if key else None
    if not payload:
        return dict(FREE_PLAN)
    return {
        "plan": payload.get("plan", "pro"),
        "max_hosts": payload["max_hosts"],
        "customer": payload.get("customer"),
        "expires": payload.get("expires"),
    }


def get_license() -> dict:
    return _cached_license(settings.LICENSE_KEY or "")


def max_hosts() -> int:
    return get_license()["max_hosts"]
