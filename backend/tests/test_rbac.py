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


def test_custom_role_writes_only_allowed_sections(client):
    # Admin crée un rôle personnalisé : écriture sur les hôtes uniquement.
    r = client.post(
        "/api/roles",
        json={"name": "hosts-only", "description": "Hôtes seuls", "permissions": ["hosts"]},
    )
    assert r.status_code == 201

    # Le catalogue expose sections + rôles intégrés + personnalisés.
    listing = client.get("/api/roles").json()
    assert any(s["key"] == "hosts" for s in listing["sections"])
    names = {role["name"] for role in listing["roles"]}
    assert {"admin", "operator", "viewer", "hosts-only"} <= names

    # Assignation du rôle custom à un utilisateur.
    u = client.post(
        "/api/users",
        json={"email": "custom@local", "password": "custom123", "role": "hosts-only"},
    )
    assert u.status_code == 201
    assert u.json()["role"] == "hosts-only"
    assert u.json()["is_admin"] is False

    cu = _login("custom@local", "custom123")
    # Autorisé sur les hôtes...
    assert cu.post(
        "/api/hosts", json={"name": "c-host", "hostname_or_ip": "3.3.3.3"}
    ).status_code == 201
    # ...mais refusé sur une section non accordée (tickets).
    assert cu.post(
        "/api/tickets", json={"title": "x", "priority": "medium"}
    ).status_code == 403
    # Lecture toujours ouverte.
    assert cu.get("/api/tickets").status_code == 200


def test_cannot_create_role_with_builtin_name(client):
    assert client.post("/api/roles", json={"name": "admin", "permissions": []}).status_code == 400


def test_assign_unknown_role_rejected(client):
    resp = client.post(
        "/api/users",
        json={"email": "bad@local", "password": "bad12345", "role": "does-not-exist"},
    )
    assert resp.status_code == 400
