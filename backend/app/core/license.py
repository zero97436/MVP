"""Licence : version gratuite limitée à 100 hôtes, déblocable par clé signée.

Format de clé : base64url(payload_json) + "." + hmac_sha256(payload, VENDOR_KEY)
payload : {"plan": "pro", "max_hosts": 1000, "customer": "...", "expires": "2027-01-01"}

La clé se génère avec scripts/generate_license.py (nécessite la clé vendeur,
jamais distribuée). Une clé invalide/expirée est ignorée -> retour au plan free.

⚠️ Logiciel auto-hébergé : ceci est une barrière commerciale honnête, pas du DRM
   incassable (l'utilisateur a le code). C'est le même modèle que GitLab CE/EE.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import date
from functools import lru_cache

from app.core.config import settings

# Clé de vérification embarquée (la clé de GÉNÉRATION reste chez l'éditeur —
# ici HMAC symétrique : générer des clés exige cette valeur, gardée privée
# dans le dépôt de l'éditeur ; changez-la avant toute distribution publique).
VENDOR_KEY = b"supervision-house-vendor-2026-Kf8mQ2xVw9"

FREE_PLAN = {"plan": "free", "max_hosts": 100, "customer": None, "expires": None}


def _verify(key: str) -> dict | None:
    try:
        payload_b64, sig = key.strip().split(".")
        payload_raw = base64.urlsafe_b64decode(payload_b64 + "==")
        expected = hmac.new(VENDOR_KEY, payload_raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            return None
        payload = json.loads(payload_raw)
        expires = payload.get("expires")
        if expires and date.fromisoformat(expires) < date.today():
            return None  # licence expirée
        if not isinstance(payload.get("max_hosts"), int) or payload["max_hosts"] < 1:
            return None
        return payload
    except Exception:  # noqa: BLE001 — clé malformée = plan free
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
