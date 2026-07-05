"""Vérifie que les fonctionnalités payantes sont bien verrouillées par plan."""
import pytest

import app.core.license as lic


def _set_plan(monkeypatch, plan: str):
    monkeypatch.setattr(lic, "get_license", lambda: {
        "plan": plan, "max_hosts": 500 if plan == "community" else None,
        "features": sorted(lic.PLAN_FEATURES[plan]), "customer": None, "expires": None,
    })


@pytest.fixture
def community(client, monkeypatch):
    _set_plan(monkeypatch, "community")
    return client


@pytest.fixture
def professional(client, monkeypatch):
    _set_plan(monkeypatch, "professional")
    return client


def test_community_blocks_pro_features(community):
    # Rapports SLA / MTTR / PDF -> Professional.
    assert community.get("/api/reports/sla").status_code == 403
    assert community.get("/api/reports/mttr").status_code == 403
    r = community.get("/api/reports/pdf")
    assert r.status_code == 403
    assert "Professional" in r.json()["detail"]

    # Dashboards personnalisables -> Professional (lecture reste ouverte).
    assert community.get("/api/dashboard/layout").status_code == 200
    assert community.put("/api/dashboard/layout",
                         json={"sections": [{"id": "hero", "visible": True}]}).status_code == 403

    # Canaux avancés -> Professional ; e-mail et webhook restent Community.
    assert community.post("/api/settings/notification-channels",
                          json={"name": "slack", "type": "slack", "config_json": {"webhook_url": "https://x"}},
                          ).status_code == 403
    assert community.post("/api/settings/notification-channels",
                          json={"name": "mail-noc", "type": "email", "config_json": {"to": "noc@x.fr"}},
                          ).status_code in (200, 201)


def test_community_blocks_business_features(community):
    # Supervision distribuée (sonde) -> Business.
    host = community.post("/api/hosts", json={"name": "gate-h", "hostname_or_ip": "10.0.1.50"}).json()["id"]
    r = community.post("/api/checks", json={
        "host_id": host, "name": "via sonde", "type": "ping", "executor_host_id": host,
    })
    assert r.status_code == 403 and "Business" in r.json()["detail"]
    # Sans sonde : OK.
    assert community.post("/api/checks", json={
        "host_id": host, "name": "central", "type": "ping",
    }).status_code == 201

    # Automatisation de remédiation -> Business.
    assert community.post("/api/dashboard/incidents/1/remediate",
                          json={"action": "restart"}).status_code == 403


def test_professional_unlocks_pro_but_not_business(professional):
    assert professional.get("/api/reports/sla").status_code == 200
    assert professional.get("/api/reports/pdf").status_code == 200
    assert professional.post("/api/settings/notification-channels",
                             json={"name": "tg", "type": "telegram",
                                   "config_json": {"bot_token": "x", "chat_id": "1"}},
                             ).status_code in (200, 201)
    # Mais pas la remédiation (Business).
    r = professional.post("/api/dashboard/incidents/1/remediate", json={"action": "restart"})
    assert r.status_code == 403


def test_plans_are_cumulative():
    assert lic.PLAN_FEATURES["professional"] < lic.PLAN_FEATURES["business"]
    assert lic.PLAN_FEATURES["business"] < lic.PLAN_FEATURES["enterprise"]
    # Chaque feature connaît son plan d'entrée (pour les messages d'upgrade).
    assert lic.FEATURE_PLAN["sla_reports"] == "professional"
    assert lic.FEATURE_PLAN["itsm_connectors"] == "business"
    assert lic.FEATURE_PLAN["sso"] == "enterprise"


def test_community_host_limit_is_500():
    assert lic.COMMUNITY_PLAN["max_hosts"] == 500