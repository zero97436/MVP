from app.api.routes.auth import _make_reset_token
from app.models.user import User


def _make_user(client, db, email="reset@local", pw="Password123"):
    from app.core.security import hash_password
    u = db.query(User).filter_by(email=email).first()
    if not u:
        u = User(email=email, hashed_password=hash_password(pw), is_active=True, role="viewer")
        db.add(u)
        db.commit()
        db.refresh(u)
    return u


def test_forgot_password_always_neutral(client):
    # E-mail inexistant -> réponse neutre (anti-énumération), pas d'erreur.
    r = client.post("/api/auth/forgot-password", json={"email": "inconnu@nowhere.fr"})
    assert r.status_code == 200 and r.json()["ok"] is True


def test_reset_password_flow(client, db):
    u = _make_user(client, db, "reset1@local", "OldPass123")
    token = _make_reset_token(u)

    # Réinitialisation OK.
    assert client.post("/api/auth/reset-password", json={"token": token, "new_password": "NewPass456"}).json()["ok"] is True

    # Le nouveau mot de passe fonctionne, l'ancien non.
    assert client.post("/api/auth/login", json={"email": "reset1@local", "password": "NewPass456"}).status_code == 200
    assert client.post("/api/auth/login", json={"email": "reset1@local", "password": "OldPass123"}).status_code == 401


def test_reset_token_is_single_use(client, db):
    u = _make_user(client, db, "reset2@local", "OldPass123")
    token = _make_reset_token(u)
    assert client.post("/api/auth/reset-password", json={"token": token, "new_password": "First789"}).status_code == 200
    # Le même lien ne peut pas être réutilisé (empreinte du mot de passe changée).
    r = client.post("/api/auth/reset-password", json={"token": token, "new_password": "Second999"})
    assert r.status_code == 400


def test_reset_rejects_bad_token(client):
    assert client.post("/api/auth/reset-password", json={"token": "n.importe.quoi", "new_password": "Whatever123"}).status_code == 400
