from fastapi.testclient import TestClient

from app.main import app


def _login(email: str, password: str) -> TestClient:
    c = TestClient(app)
    token = c.post("/api/auth/login", json={"email": email, "password": password}).json()[
        "access_token"
    ]
    c.headers.update({"Authorization": f"Bearer {token}"})
    return c


def test_viewer_cannot_mutate_but_can_read(client):
    # admin (client) crée un viewer
    resp = client.post(
        "/api/users",
        json={"email": "viewer@local", "password": "viewer123", "role": "viewer"},
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "viewer"

    viewer = _login("viewer@local", "viewer123")
    # Lecture autorisée
    assert viewer.get("/api/hosts").status_code == 200
    # Mutation interdite
    assert viewer.post(
        "/api/hosts", json={"name": "x", "hostname_or_ip": "1.1.1.1"}
    ).status_code == 403


def test_operator_can_mutate_hosts_but_not_users(client):
    client.post(
        "/api/users",
        json={"email": "op@local", "password": "operator123", "role": "operator"},
    )
    op = _login("op@local", "operator123")
    # Opérateur peut créer un hôte
    assert op.post(
        "/api/hosts", json={"name": "op-host", "hostname_or_ip": "2.2.2.2"}
    ).status_code == 201
    # Mais pas gérer les utilisateurs (admin only)
    assert op.get("/api/users").status_code == 403


def test_me_exposes_role(client):
    assert client.get("/api/auth/me").json()["role"] == "admin"
