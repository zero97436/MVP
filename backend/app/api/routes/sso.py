"""SSO / OIDC (Enterprise) — Authorization Code Flow.

Compatible avec tout fournisseur OpenID Connect : Keycloak, Azure AD/Entra,
Google Workspace, Okta, Authentik…

Flux :
  1. GET /auth/sso/login    -> redirige vers le fournisseur (state signé, 10 min)
  2. le fournisseur renvoie -> GET /auth/sso/callback?code&state
  3. échange code -> token, lecture de l'e-mail via userinfo
  4. compte trouvé/créé     -> JWT Opsora -> redirection /login?sso_token=…

Sécurité : state = JWT signé (anti-CSRF, expirant) ; l'e-mail vient du endpoint
userinfo du fournisseur (TLS) ; comptes créés avec le rôle SSO_DEFAULT_ROLE.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.license import has_feature, require_feature
from app.core.logging import get_logger
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/auth/sso", tags=["sso"])


# ---- helpers (isolés pour être mockables en test) ----
def _discover(issuer: str) -> dict:
    r = httpx.get(f"{issuer.rstrip('/')}/.well-known/openid-configuration", timeout=10)
    r.raise_for_status()
    return r.json()


def _exchange_code(token_endpoint: str, code: str, redirect_uri: str) -> dict:
    r = httpx.post(token_endpoint, data={
        "grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri,
        "client_id": settings.OIDC_CLIENT_ID, "client_secret": settings.OIDC_CLIENT_SECRET,
    }, timeout=10)
    r.raise_for_status()
    return r.json()


def _userinfo(endpoint: str, access_token: str) -> dict:
    r = httpx.get(endpoint, headers={"Authorization": f"Bearer {access_token}"}, timeout=10)
    r.raise_for_status()
    return r.json()


def _configured() -> bool:
    return bool(settings.OIDC_ISSUER and settings.OIDC_CLIENT_ID)


def _callback_url(request: Request) -> str:
    """URL publique du callback (respecte le proxy nginx via X-Forwarded-*)."""
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{proto}://{host}/api/auth/sso/callback"


def _make_state(redirect_uri: str) -> str:
    return jwt.encode(
        {"n": uuid.uuid4().hex, "r": redirect_uri,
         "exp": datetime.now(timezone.utc) + timedelta(minutes=10)},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )


def _check_state(state: str) -> dict:
    try:
        return jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(400, "state SSO invalide ou expiré")


# ---- routes ----
@router.get("/info")
def sso_info():
    """PUBLIC : la page de login s'en sert pour afficher (ou non) le bouton SSO."""
    return {"enabled": has_feature("sso") and _configured()}


@router.get("/login", dependencies=[Depends(require_feature("sso"))])
def sso_login(request: Request):
    if not _configured():
        raise HTTPException(503, "SSO non configuré (OIDC_ISSUER / OIDC_CLIENT_ID)")
    conf = _discover(settings.OIDC_ISSUER)
    redirect_uri = _callback_url(request)
    params = urlencode({
        "response_type": "code",
        "client_id": settings.OIDC_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "openid email profile",
        "state": _make_state(redirect_uri),
    })
    return RedirectResponse(f"{conf['authorization_endpoint']}?{params}", status_code=302)


@router.get("/callback", dependencies=[Depends(require_feature("sso"))])
def sso_callback(code: str = "", state: str = "", error: str = "", db: Session = Depends(get_db)):
    if error:
        return RedirectResponse(f"/login?sso_error=Fournisseur : {error[:80]}", status_code=302)
    if not code or not state:
        raise HTTPException(400, "code/state manquants")
    payload = _check_state(state)

    try:
        conf = _discover(settings.OIDC_ISSUER)
        tokens = _exchange_code(conf["token_endpoint"], code, payload["r"])
        info = _userinfo(conf["userinfo_endpoint"], tokens["access_token"])
    except Exception as exc:  # noqa: BLE001
        logger.warning("SSO : échange OIDC échoué : %s", exc)
        return RedirectResponse("/login?sso_error=Échange avec le fournisseur impossible", status_code=302)

    email = (info.get("email") or "").strip().lower()
    if not email:
        return RedirectResponse("/login?sso_error=Le fournisseur n'a pas transmis d'e-mail", status_code=302)
    if info.get("email_verified") is False:
        return RedirectResponse("/login?sso_error=E-mail non vérifié chez le fournisseur", status_code=302)

    user = db.query(User).filter(User.email == email).first()
    if user and not user.is_active:
        return RedirectResponse("/login?sso_error=Compte désactivé", status_code=302)
    if not user:
        if not settings.SSO_AUTO_CREATE_USERS:
            return RedirectResponse("/login?sso_error=Compte inconnu (création SSO désactivée)", status_code=302)
        user = User(
            email=email,
            full_name=(info.get("name") or "")[:255] or None,
            hashed_password="!sso!",  # jamais un hash valide -> login mot de passe impossible
            is_active=True, is_admin=False,
            role=settings.SSO_DEFAULT_ROLE if settings.SSO_DEFAULT_ROLE in ("admin", "operator", "viewer") else "viewer",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("SSO : compte créé pour %s (rôle %s)", email, user.role)

    token = create_access_token(subject=user.email)
    return RedirectResponse(f"/login?sso_token={token}", status_code=302)
