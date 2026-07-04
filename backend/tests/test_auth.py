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
