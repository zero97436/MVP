from urllib.parse import parse_qs, urlparse

import app.core.license as lic
from app.api.routes.sso import _make_state
from app.models.user import User

CONF = {
    "authorization_endpoint": "https://idp.acme.fr/authorize",
    "token_endpoint": "https://idp.acme.fr/token",
    "userinfo_endpoint": "https://idp.acme.fr/userinfo",
}


def _configure(monkeypatch, email="jane@acme.fr", name="Jane Doe", verified=True):
    from app.core.config import settings as cfg

    monkeypatch.setattr(cfg, "OIDC_ISSUER", "https://idp.acme.fr")
    monkeypatch.setattr(cfg, "OIDC_CLIENT_ID", "opsora")
    monkeypatch.setattr(cfg, "OIDC_CLIENT_SECRET", "s3cret")
    monkeypatch.setattr("app.api.routes.sso._discover", lambda issuer: CONF)
    monkeypatch.setattr("app.api.routes.sso._exchange_code",
                        lambda te, code, ru: {"access_token": "at-123"})
    monkeypatch.setattr("app.api.routes.sso._userinfo",
                        lambda ep, at: {"email": email, "name": name, "email_verified": verified})


def test_sso_info_disabled_by_default(client):
    assert client.get("/api/auth/sso/info").json() == {"enabled": False}


def test_sso_info_enabled_when_configured(client, monkeypatch):
    _configure(monkeypatch)
    assert client.get("/api/auth/sso/info").json() == {"enabled": True}


def test_sso_login_redirects_to_provider(client, monkeypatch):
    _configure(monkeypatch)
    r = client.get("/api/auth/sso/login", follow_redirects=False)
    assert r.status_code == 302
    url = urlparse(r.headers["location"])
    assert url.netloc == "idp.acme.fr" and url.path == "/authorize"
    q = parse_qs(url.query)
    assert q["client_id"] == ["opsora"]
    assert q["response_type"] == ["code"]
    assert "state" in q and "openid" in q["scope"][0]


def test_sso_callback_creates_user_and_logs_in(client, db, monkeypatch):
    _configure(monkeypatch, email="Nouvelle@Acme.fr", name="Nouvelle Recrue")
    state = _make_state("https://opsora.acme.fr/api/auth/sso/callback")
    r = client.get("/api/auth/sso/callback", params={"code": "abc", "state": state},
                   follow_redirects=False)
    assert r.status_code == 302
    assert "sso_token=" in r.headers["location"]

    user = db.query(User).filter_by(email="nouvelle@acme.fr").first()  # normalisé en minuscules
    assert user is not None
    assert user.role == "viewer"          # rôle par défaut SSO
    assert user.full_name == "Nouvelle Recrue"
    assert user.hashed_password == "!sso!"  # login par mot de passe impossible

    # Le token émis fonctionne sur l'API.
    token = r.headers["location"].split("sso_token=")[1]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["email"] == "nouvelle@acme.fr"


def test_sso_callback_existing_user_keeps_role(client, db, monkeypatch):
    _configure(monkeypatch, email="admin@local")  # le compte admin existant
    state = _make_state("x")
    r = client.get("/api/auth/sso/callback", params={"code": "abc", "state": state},
                   follow_redirects=False)
    assert "sso_token=" in r.headers["location"]
    assert db.query(User).filter_by(email="admin@local").first().role == "admin"  # inchangé


def test_sso_callback_guards(client, monkeypatch):
    from app.core.config import settings as cfg

    _configure(monkeypatch, verified=False)
    state = _make_state("x")
    r = client.get("/api/auth/sso/callback", params={"code": "a", "state": state}, follow_redirects=False)
    assert "sso_error" in r.headers["location"]  # e-mail non vérifié

    # state falsifié -> 400.
    assert client.get("/api/auth/sso/callback",
                      params={"code": "a", "state": "forge.xx.yy"}).status_code == 400

    # auto-création désactivée -> erreur propre.
    _configure(monkeypatch, email="inconnu@acme.fr")
    monkeypatch.setattr(cfg, "SSO_AUTO_CREATE_USERS", False)
    r = client.get("/api/auth/sso/callback", params={"code": "a", "state": _make_state("x")},
                   follow_redirects=False)
    assert "sso_error" in r.headers["location"]


def test_sso_requires_enterprise_plan(client, monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr(lic, "get_license", lambda: {
        "plan": "professional", "max_hosts": None,
        "features": sorted(lic.PLAN_FEATURES["professional"]), "customer": None, "expires": None,
    })
    # info -> désactivé (pas de bouton), login -> 403 Enterprise.
    assert client.get("/api/auth/sso/info").json() == {"enabled": False}
    r = client.get("/api/auth/sso/login", follow_redirects=False)
    assert r.status_code == 403 and "Enterprise" in r.json()["detail"]
