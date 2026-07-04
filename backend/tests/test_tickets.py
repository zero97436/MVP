from app.models.alert import Alert


def _make_alert(client, db) -> int:
    host = client.post("/api/hosts", json={"name": "tk-host", "hostname_or_ip": "10.0.9.1"}).json()["id"]
    cid = client.post("/api/checks", json={"host_id": host, "name": "web", "type": "ping"}).json()["id"]
    alert = Alert(check_id=cid, status="CRITICAL", is_active=True)
    db.add(alert)
    db.commit()
    return alert.id


def test_ticket_manual_create_and_list(client):
    r = client.post("/api/tickets", json={"title": "Disque plein sur srv1", "priority": "high"})
    assert r.status_code == 201
    t = r.json()
    assert t["title"] == "Disque plein sur srv1"
    assert t["status"] == "open" and t["priority"] == "high"
    assert t["provider"] == "internal"  # défaut en test

    tickets = client.get("/api/tickets").json()
    assert any(x["id"] == t["id"] for x in tickets)


def test_ticket_from_incident(client, db):
    alert_id = _make_alert(client, db)
    r = client.post("/api/tickets", json={"alert_id": alert_id})
    assert r.status_code == 201
    t = r.json()
    assert t["alert_id"] == alert_id
    assert t["priority"] == "critical"  # dérivé du statut CRITICAL
    # Titre : « Hôte : sujet »
    assert t["title"].startswith("tk-host : ")
    assert "Incident sur web" in t["title"]
    # Corps rédigé comme un mail.
    assert t["description"].startswith("Bonjour,")
    assert "tk-host" in t["description"] and "web" in t["description"]
    assert t["description"].rstrip().endswith("La supervision")
    assert "Cordialement," in t["description"]


def test_ticket_tasks_crud(client):
    t = client.post("/api/tickets", json={"title": "Serveur : maintenance"}).json()
    assert t["tasks"] == []

    t1 = client.post(f"/api/tickets/{t['id']}/tasks", json={"label": "Vérifier les sauvegardes"}).json()
    t2 = client.post(f"/api/tickets/{t['id']}/tasks", json={"label": "Redémarrer le service"}).json()
    assert client.post(f"/api/tickets/{t['id']}/tasks", json={"label": "  "}).status_code == 400

    # Cocher la première tâche.
    r = client.patch(f"/api/tickets/tasks/{t1['id']}", json={"done": True})
    assert r.json()["done"] is True

    # Les tâches remontent dans le ticket, dans l'ordre.
    tk = next(x for x in client.get("/api/tickets").json() if x["id"] == t["id"])
    assert [x["label"] for x in tk["tasks"]] == ["Vérifier les sauvegardes", "Redémarrer le service"]
    assert tk["tasks"][0]["done"] is True and tk["tasks"][1]["done"] is False

    # Renommer puis supprimer.
    assert client.patch(f"/api/tickets/tasks/{t2['id']}", json={"label": "Relancer nginx"}).json()["label"] == "Relancer nginx"
    assert client.delete(f"/api/tickets/tasks/{t2['id']}").status_code == 204
    assert client.delete(f"/api/tickets/tasks/{t2['id']}").status_code == 404

    # Suppression du ticket -> tâches en cascade.
    assert client.delete(f"/api/tickets/{t['id']}").status_code == 204


def test_ticket_status_workflow(client):
    t = client.post("/api/tickets", json={"title": "Ticket X"}).json()
    assert client.patch(f"/api/tickets/{t['id']}", json={"status": "in_progress"}).json()["status"] == "in_progress"
    assert client.patch(f"/api/tickets/{t['id']}", json={"status": "closed"}).json()["status"] == "closed"
    # statut invalide ignoré (reste closed)
    assert client.patch(f"/api/tickets/{t['id']}", json={"status": "bogus"}).json()["status"] == "closed"

    # filtre par statut
    closed = client.get("/api/tickets", params={"status": "closed"}).json()
    assert all(x["status"] == "closed" for x in closed)


def test_ticket_validation_and_delete(client):
    assert client.post("/api/tickets", json={}).status_code == 400  # ni title ni alert_id
    t = client.post("/api/tickets", json={"title": "à supprimer"}).json()
    assert client.delete(f"/api/tickets/{t['id']}").status_code == 204
    assert client.patch(f"/api/tickets/{t['id']}", json={"status": "open"}).status_code == 404


def test_ticket_config(client):
    cfg = client.get("/api/tickets/config").json()
    assert cfg["provider"] == "internal"
    assert cfg["target"] == "local"


def test_ticket_full_edit_glpi_like(client):
    t = client.post("/api/tickets", json={"title": "Ancien titre", "description": "desc", "priority": "low"}).json()

    r = client.patch(f"/api/tickets/{t['id']}", json={
        "title": "Serveur : nouveau titre", "description": "Nouvelle description",
        "priority": "high", "status": "in_progress",
    })
    assert r.status_code == 200
    out = r.json()
    assert out["title"] == "Serveur : nouveau titre"
    assert out["description"] == "Nouvelle description"
    assert out["priority"] == "high" and out["status"] == "in_progress"
    # La modification est journalisée dans les suivis.
    assert len(out["comments"]) == 1
    assert "Modification" in out["comments"][0]["body"]
    assert "titre" in out["comments"][0]["body"]

    # Valeurs invalides ignorées, sans erreur.
    out2 = client.patch(f"/api/tickets/{t['id']}", json={"priority": "bogus", "status": "bogus"}).json()
    assert out2["priority"] == "high" and out2["status"] == "in_progress"


def test_ticket_assignment(client):
    users = client.get("/api/tickets/assignees").json()
    assert users and all("email" in u for u in users)
    admin = next(u for u in users if u["email"] == "admin@local")

    t = client.post("/api/tickets", json={"title": "À assigner"}).json()
    assert t["assigned_to"] is None

    # Assigner.
    out = client.patch(f"/api/tickets/{t['id']}", json={"assigned_to_id": admin["id"]}).json()
    assert out["assigned_to_id"] == admin["id"]
    assert out["assigned_to"] == "admin@local"
    assert any("assigné à admin@local" in c["body"] for c in out["comments"])  # journalisé

    # Utilisateur inexistant -> ignoré sans erreur.
    out = client.patch(f"/api/tickets/{t['id']}", json={"assigned_to_id": 99999}).json()
    assert out["assigned_to_id"] == admin["id"]

    # Désassigner (null explicite).
    out = client.patch(f"/api/tickets/{t['id']}", json={"assigned_to_id": None}).json()
    assert out["assigned_to_id"] is None
    assert any("désassigné" in c["body"] for c in out["comments"])

    # PATCH sans le champ -> assignation inchangée.
    client.patch(f"/api/tickets/{t['id']}", json={"assigned_to_id": admin["id"]})
    out = client.patch(f"/api/tickets/{t['id']}", json={"priority": "high"}).json()
    assert out["assigned_to_id"] == admin["id"]


def test_ticket_assignment_notification(client, monkeypatch):
    """L'assigné reçoit un e-mail — sauf auto-assignation ; un échec SMTP ne bloque rien."""
    sent = []
    monkeypatch.setattr(
        "app.notifications.email_notifier.EmailNotifier.send",
        lambda self, notification, config: sent.append((notification.subject, config["to"])) or True,
    )
    # Un second utilisateur à qui assigner.
    other = client.post("/api/users", json={
        "email": "tech@local", "password": "Password123!", "role": "operator", "full_name": "Tech",
    }).json()

    t = client.post("/api/tickets", json={"title": "Routeur : à vérifier"}).json()
    client.patch(f"/api/tickets/{t['id']}", json={"assigned_to_id": other["id"]})
    assert len(sent) == 1
    subject, to = sent[0]
    assert to == "tech@local"
    assert f"#{t['id']}" in subject and "Routeur" in subject

    # Auto-assignation (admin s'assigne lui-même) -> pas de mail.
    admin = next(u for u in client.get("/api/tickets/assignees").json() if u["email"] == "admin@local")
    client.patch(f"/api/tickets/{t['id']}", json={"assigned_to_id": admin["id"]})
    assert len(sent) == 1  # inchangé

    # Échec d'envoi -> l'assignation reste effective.
    monkeypatch.setattr(
        "app.notifications.email_notifier.EmailNotifier.send",
        lambda self, notification, config: (_ for _ in ()).throw(RuntimeError("smtp down")),
    )
    out = client.patch(f"/api/tickets/{t['id']}", json={"assigned_to_id": other["id"]}).json()
    assert out["assigned_to"] == "tech@local"


def test_ticket_comments(client):
    t = client.post("/api/tickets", json={"title": "Avec suivis"}).json()
    c1 = client.post(f"/api/tickets/{t['id']}/comments", json={"body": "Pris en charge, diagnostic en cours."})
    assert c1.status_code == 201
    assert c1.json()["author"]  # auteur = utilisateur connecté
    assert client.post(f"/api/tickets/{t['id']}/comments", json={"body": "  "}).status_code == 400

    tk = next(x for x in client.get("/api/tickets").json() if x["id"] == t["id"])
    assert len(tk["comments"]) == 1
    assert tk["comments"][0]["body"].startswith("Pris en charge")

    assert client.delete(f"/api/tickets/comments/{c1.json()['id']}").status_code == 204
    assert client.delete(f"/api/tickets/comments/{c1.json()['id']}").status_code == 404


def _make_check(client, ip):
    host = client.post("/api/hosts", json={"name": f"auto-{ip}", "hostname_or_ip": ip}).json()["id"]
    return client.post("/api/checks", json={"host_id": host, "name": "svc", "type": "ping"}).json()["id"]


def test_ticket_dedupe_same_check(client, db):
    """Deux incidents successifs sur le même check -> UN SEUL ticket ouvert."""
    from app.services.ticket_service import TicketService

    cid = _make_check(client, "10.0.9.10")
    a1 = Alert(check_id=cid, status="CRITICAL", is_active=True)
    a2 = Alert(check_id=cid, status="CRITICAL", is_active=True)
    db.add_all([a1, a2])
    db.commit()

    svc = TicketService(db)
    t1 = svc.create_from_alert(a1, created_by="auto")
    t2 = svc.create_from_alert(a2, created_by="auto")
    assert t1.id == t2.id  # pas de doublon
    assert t2.alert_id == a2.id  # rattaché à l'alerte la plus récente

    # Ticket clôturé -> un nouvel incident recrée bien un ticket.
    svc.update_status(t1.id, "closed")
    a3 = Alert(check_id=cid, status="CRITICAL", is_active=True)
    db.add(a3)
    db.commit()
    t3 = svc.create_from_alert(a3, created_by="auto")
    assert t3.id != t1.id


def test_ticket_auto_create_on_incident(client, db, monkeypatch):
    """Passage CRITICAL -> ticket auto ; re-CRITICAL -> pas de doublon ; retour OK -> résolu."""
    from app.core.config import settings as cfg
    from app.models.check import Check
    from app.models.ticket import Ticket
    from app.services.alert_service import AlertService

    monkeypatch.setattr(cfg, "ITSM_AUTO_CREATE", True)
    cid = _make_check(client, "10.0.9.11")
    check = db.get(Check, cid)

    AlertService(db).handle_status_change(check, "CRITICAL", "OK", "down")
    tickets = db.query(Ticket).join(Alert, Alert.id == Ticket.alert_id).filter(Alert.check_id == cid).all()
    assert len(tickets) == 1
    assert tickets[0].created_by == "auto" and tickets[0].status == "open"

    # Flapping : nouvel incident -> toujours 1 seul ticket ouvert.
    AlertService(db).handle_status_change(check, "OK", "CRITICAL", "up")     # résout
    db.refresh(tickets[0])
    assert tickets[0].status == "resolved"  # auto-résolu au retour OK

    AlertService(db).handle_status_change(check, "CRITICAL", "OK", "down")  # nouveau ticket
    AlertService(db).handle_status_change(check, "WARNING", "CRITICAL", "meh")
    open_tickets = (
        db.query(Ticket).join(Alert, Alert.id == Ticket.alert_id)
        .filter(Alert.check_id == cid, Ticket.status == "open").all()
    )
    assert len(open_tickets) == 1  # anti-doublon même en flapping
