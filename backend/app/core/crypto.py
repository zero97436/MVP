"""Chiffrement des secrets au repos (Fernet, clé dérivée de SECRET_KEY).

On chiffre uniquement les champs sensibles d'un config_json (mots de passe, tokens…),
en laissant les autres clés lisibles. Les valeurs chiffrées sont préfixées 'enc:'.
Les anciennes valeurs en clair sont gérées gracieusement (déchiffrement = no-op).
"""
import base64
import hashlib
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

# Champs considérés comme secrets dans les config_json.
SECRET_FIELDS = {"password", "bot_token", "token", "secret", "webhook_url", "api_key", "auth_token", "token_secret"}
ENC_PREFIX = "enc:"
REDACTION = "********"


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key)


def encrypt_value(plaintext: str) -> str:
    return ENC_PREFIX + _fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(value: str) -> str:
    if not isinstance(value, str) or not value.startswith(ENC_PREFIX):
        return value  # legacy clair ou non chiffré
    try:
        return _fernet().decrypt(value[len(ENC_PREFIX):].encode()).decode()
    except (InvalidToken, ValueError):
        return value


def encrypt_config(cfg: dict[str, Any] | None) -> dict[str, Any]:
    """Chiffre les champs secrets en clair (laisse les déjà-chiffrés et les non-secrets)."""
    if not cfg:
        return cfg or {}
    out = dict(cfg)
    for k, v in out.items():
        if k in SECRET_FIELDS and isinstance(v, str) and v and not v.startswith(ENC_PREFIX):
            out[k] = encrypt_value(v)
    return out


def merge_secret_config(new: dict[str, Any] | None, old: dict[str, Any] | None) -> dict[str, Any]:
    """À la mise à jour : si un champ secret arrive masqué/vide, on conserve l'ancienne
    valeur chiffrée ; sinon on (re)chiffre la nouvelle."""
    new = dict(new or {})
    old = old or {}
    for k in SECRET_FIELDS:
        if k in new and (new[k] == REDACTION or new[k] == "" or new[k] is None):
            if old.get(k) is not None:
                new[k] = old[k]
            else:
                new.pop(k, None)
    return encrypt_config(new)


def decrypt_config(cfg: dict[str, Any] | None) -> dict[str, Any]:
    """Déchiffre les champs secrets pour usage (exécution de check, envoi de notif)."""
    if not cfg:
        return cfg or {}
    return {k: (decrypt_value(v) if k in SECRET_FIELDS else v) for k, v in cfg.items()}


def redact_config(cfg: dict[str, Any] | None) -> dict[str, Any]:
    """Masque les champs secrets pour les réponses API (UI ne reçoit jamais le clair)."""
    if not cfg:
        return cfg or {}
    return {k: (REDACTION if (k in SECRET_FIELDS and v) else v) for k, v in cfg.items()}
