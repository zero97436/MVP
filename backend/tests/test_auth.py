def test_login_success(client):
    resp = client.post(
        "/api/auth/login", json={"email": "admin@local", "password": "admin1234"}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    resp = client.post(
        "/api/auth/login", json={"email": "admin@local", "password": "wrong"}
    )
    assert resp.status_code == 401


def test_me(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@local"


def test_protected_requires_auth():
    from fastapi.testclient import TestClient
    from app.main import app

    resp = TestClient(app).get("/api/hosts")
    assert resp.status_code == 401


def test_change_own_password(client):
    # Mauvais mot de passe actuel -> 400.
    assert client.post("/api/auth/change-password",
                       json={"current_password": "faux", "new_password": "Nouveau123"}).status_code == 400
    # Identique -> 400.
    assert client.post("/api/auth/change-password",
                       json={"current_password": "admin1234", "new_password": "admin1234"}).status_code == 400
    # Changement OK.
    assert client.post("/api/auth/change-password",
                       json={"current_password": "admin1234", "new_password": "Nouveau123"}).json()["ok"] is True

    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    # L'ancien ne marche plus, le nouveau oui.
    assert c.post("/api/auth/login", json={"email": "admin@local", "password": "admin1234"}).status_code == 401
    login = c.post("/api/auth/login", json={"email": "admin@local", "password": "Nouveau123"})
    assert login.status_code == 200

    # Restaure le mot de passe admin (base partagée entre tests).
    tok = login.json()["access_token"]
    c.headers.update({"Authorization": f"Bearer {tok}"})
    assert c.post("/api/auth/change-password",
                  json={"current_password": "Nouveau123", "new_password": "admin1234"}).json()["ok"] is True
