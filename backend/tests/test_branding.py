from fastapi.testclient import TestClient

import app.core.license as lic
from app.main import app


def test_branding_default_public(client):
    """Lisible SANS authentification (login/status en ont besoin)."""
    r = TestClient(app).get("/api/branding")
    assert r.status_code == 200
    data = r.json()
    assert data["display_name"] == "Opsora"
    assert data["custom"] is False


def test_branding_set_and_reset(client):
    r = client.put("/api/branding", json={
        "display_name": "Supervision ACME", "tagline": "Votre infra sous contrôle",
        "logo_url": "https://acme.fr/logo.png", "accent_color": "#7C3AED",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["display_name"] == "Supervision ACME"
    assert data["accent_color"] == "#7C3AED"
    assert data["custom"] is True

    # Visible publiquement (page de login).
    assert TestClient(app).get("/api/branding").json()["display_name"] == "Supervision ACME"

    # Validation.
    assert client.put("/api/branding", json={"accent_color": "rouge"}).status_code == 400
    assert client.put("/api/branding", json={"logo_url": "javascript:alert(1)"}).status_code == 400

    # Reset -> retour Opsora.
    assert client.delete("/api/branding").status_code == 204
    assert TestClient(app).get("/api/branding").json()["custom"] is False


def test_branding_requires_pro_plan(client, monkeypatch):
    # Personnalisation enregistrée en licence complète…
    client.put("/api/branding", json={"display_name": "ACME"})

    # …mais en Community : écriture refusée ET lecture = identité par défaut
    # (la personnalisation ne survit pas à une licence expirée).
    monkeypatch.setattr(lic, "get_license", lambda: {
        "plan": "community", "max_hosts": 500, "features": [], "customer": None, "expires": None,
    })
    r = client.put("/api/branding", json={"display_name": "Pirate"})
    assert r.status_code == 403 and "Professional" in r.json()["detail"]
    assert TestClient(app).get("/api/branding").json()["display_name"] == "Opsora"

    client.delete("/api/branding")  # nettoyage (community: delete reste admin-only, autorisé)


def test_retention_clamped_in_community(monkeypatch):
    from app.core.config import settings as cfg
    from app.services.retention_service import retention_days

    monkeypatch.setattr(cfg, "RETENTION_CHECK_RESULTS_DAYS", 365)
    # Community : plafonné à 30 jours.
    monkeypatch.setattr(lic, "get_license", lambda: {
        "plan": "community", "max_hosts": 500, "features": [], "customer": None, "expires": None,
    })
    assert retention_days("RETENTION_CHECK_RESULTS_DAYS") == 30
    # Professional (extended_retention) : la valeur configurée s'applique.
    monkeypatch.setattr(lic, "get_license", lambda: {
        "plan": "professional", "max_hosts": None,
        "features": sorted(lic.PLAN_FEATURES["professional"]), "customer": None, "expires": None,
    })
    assert retention_days("RETENTION_CHECK_RESULTS_DAYS") == 365
