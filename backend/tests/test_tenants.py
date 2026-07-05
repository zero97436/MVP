"""Multi-tenant : un utilisateur cloisonné ne voit QUE les données de son tenant."""
import pytest
from fastapi.testclient import TestClient

import app.core.license as lic
from app.main import app


_seq = [0]


@pytest.fixture
def msp(client):
    """Client admin global (voit tout) + 2 tenants + hôtes assignés (uniques par test)."""
    _seq[0] += 1
    n = _seq[0]
    a = client.post("/api/tenants", json={"name": f"Client A{n}", "slug": f"a{n}"}).json()
    b = client.post("/api/tenants", json={"name": f"Client B{n}", "slug": f"b{n}"}).json()
    ha = client.post("/api/hosts", json={"name": f"srv-A{n}", "hostname_or_ip": f"10.1.0.{n}"}).json()["id"]
    hb = client.post("/api/hosts", json={"name": f"srv-B{n}", "hostname_or_ip": f"10.2.0.{n}"}).json()["id"]
    client.post("/api/tenants/assign-host", json={"host_id": ha, "tenant_id": a["id"]})
    client.post("/api/tenants/assign-host", json={"host_id": hb, "tenant_id": b["id"]})
    return {"a": a, "b": b, "ha": ha, "hb": hb, "na": f"srv-A{n}", "nb": f"srv-B{n}", "n": n}


def _tenant_client(client, email, tenant_id):
    """Crée un utilisateur operator cloisonné et renvoie un client authentifié."""
    client.post("/api/users", json={"email": email, "password": "Password123!", "role": "operator"})
    users = client.get("/api/users").json()
    uid = next(u["id"] for u in users if u["email"] == email)
    client.post("/api/tenants/assign-user", json={"user_id": uid, "tenant_id": tenant_id})
    c = TestClient(app)
    tok = c.post("/api/auth/login", json={"email": email, "password": "Password123!"}).json()["access_token"]
    c.headers.update({"Authorization": f"Bearer {tok}"})
    return c


def test_tenant_user_sees_only_own_hosts(client, msp):
    ca = _tenant_client(client, "user-a@acme.fr", msp["a"]["id"])
    hosts = ca.get("/api/hosts").json()
    names = {h["name"] for h in hosts}
    assert names == {msp["na"]}                     # pas srv-B
    # Accès direct à l'hôte de l'autre tenant -> 404 (pas de fuite d'existence).
    assert ca.get(f"/api/hosts/{msp['hb']}").status_code == 404
    assert ca.get(f"/api/hosts/{msp['ha']}").status_code == 200


def test_tenant_user_cannot_touch_other_tenant(client, msp):
    ca = _tenant_client(client, "user-a2@acme.fr", msp["a"]["id"])
    # Créer un check sur l'hôte de B -> refusé.
    assert ca.post("/api/checks", json={"host_id": msp["hb"], "name": "x", "type": "ping"}).status_code == 404
    # Supprimer l'hôte de B -> refusé.
    assert ca.delete(f"/api/hosts/{msp['hb']}").status_code == 404


def test_new_host_auto_assigned_to_creator_tenant(client, msp):
    ca = _tenant_client(client, "user-a3@acme.fr", msp["a"]["id"])
    hid = ca.post("/api/hosts", json={"name": f"srv-A2-{msp['n']}", "hostname_or_ip": f"10.1.9.{msp['n']}"}).json()["id"]
    # Visible par lui…
    assert any(h["id"] == hid for h in ca.get("/api/hosts").json())
    # …et rattaché au bon tenant (vu par l'admin global).
    assert client.get(f"/api/hosts/{hid}").json()["tenant_id"] == msp["a"]["id"]


def test_dashboard_and_checks_scoped(client, msp):
    client.post("/api/checks", json={"host_id": msp["ha"], "name": f"ping-A{msp['n']}", "type": "ping"})
    client.post("/api/checks", json={"host_id": msp["hb"], "name": f"ping-B{msp['n']}", "type": "ping"})
    ca = _tenant_client(client, "user-a4@acme.fr", msp["a"]["id"])

    check_names = {c["name"] for c in ca.get("/api/checks").json()}
    assert f"ping-A{msp['n']}" in check_names and f"ping-B{msp['n']}" not in check_names

    summary = ca.get("/api/dashboard/summary").json()
    assert summary["hosts_total"] == 1  # uniquement srv-A


def test_global_admin_sees_everything(client, msp):
    hosts = client.get("/api/hosts").json()
    assert {msp["na"], msp["nb"]} <= {h["name"] for h in hosts}


def test_multi_tenant_disabled_without_license(client, msp, monkeypatch):
    """Sans la feature, le cloisonnement est neutre : un ex-utilisateur tenant voit tout."""
    ca = _tenant_client(client, "user-a5@acme.fr", msp["a"]["id"])
    monkeypatch.setattr(lic, "get_license", lambda: {
        "plan": "professional", "max_hosts": None,
        "features": sorted(lic.PLAN_FEATURES["professional"]), "customer": None, "expires": None,
    })
    names = {h["name"] for h in ca.get("/api/hosts").json()}
    assert {msp["na"], msp["nb"]} <= names  # plus de cloisonnement


def test_tenants_route_requires_business(client, monkeypatch):
    monkeypatch.setattr(lic, "get_license", lambda: {
        "plan": "professional", "max_hosts": None,
        "features": sorted(lic.PLAN_FEATURES["professional"]), "customer": None, "expires": None,
    })
    assert client.get("/api/tenants").status_code == 403
