"""RAG : ajout de documents, recherche (embeddings mockés + repli mots-clés)."""
from app.services.rag_service import RagService, _cosine


def test_cosine_similarity():
    assert _cosine([1, 0], [1, 0]) == 1.0
    assert abs(_cosine([1, 0], [0, 1])) < 1e-9
    assert _cosine([], [1]) == 0.0


def test_add_and_keyword_fallback(client, db, monkeypatch):
    """Sans embeddings, la recherche utilise les mots-clés."""
    monkeypatch.setattr("app.services.rag_service.embed", lambda text: None)
    svc = RagService(db)
    svc.add("Redémarrer nginx", "Pour relancer nginx : docker compose restart nginx.")
    svc.add("Sauvegarde PostgreSQL", "Lancer scripts/backup.sh pour un dump complet.")

    hits = svc.search("comment relancer nginx ?")
    assert hits and hits[0][0].title == "Redémarrer nginx"


def test_semantic_search_with_embeddings(client, db, monkeypatch):
    """Avec embeddings, la recherche utilise la similarité cosinus."""
    # Embeddings déterministes : vecteur selon un mot-clé présent.
    def fake_embed(text: str):
        t = text.lower()
        return [1.0 if "nginx" in t else 0.0, 1.0 if "backup" in t or "sauvegarde" in t else 0.0, 0.1]
    monkeypatch.setattr("app.services.rag_service.embed", fake_embed)

    svc = RagService(db)
    svc.add("Nginx", "Relancer le service nginx.")
    svc.add("Backup", "Sauvegarde de la base.")

    hits = svc.search("problème nginx 502")
    assert hits[0][0].title == "Nginx"
    assert hits[0][1] > 0.5  # forte similarité


def test_context_for_returns_sources(client, db, monkeypatch):
    monkeypatch.setattr("app.services.rag_service.embed", lambda text: None)
    RagService(db).add("Procédure disque plein", "Purger /var/log et étendre le volume.")
    context, sources = RagService(db).context_for("disque plein que faire")
    assert "Purger" in context
    assert sources and sources[0]["title"] == "Procédure disque plein"


def test_knowledge_api_crud(client):
    r = client.post("/api/knowledge", json={"title": "Runbook X", "content": "Étapes détaillées ici."})
    assert r.status_code == 201
    doc = r.json()
    assert doc["title"] == "Runbook X" and doc["chars"] > 0

    assert any(d["id"] == doc["id"] for d in client.get("/api/knowledge").json())
    assert client.post("/api/knowledge", json={"title": " ", "content": " "}).status_code == 400
    assert client.delete(f"/api/knowledge/{doc['id']}").status_code == 204
    assert client.delete(f"/api/knowledge/{doc['id']}").status_code == 404


def test_chat_injects_knowledge(client, db, monkeypatch):
    """Le chat récupère le contexte RAG et le passe au LLM."""
    monkeypatch.setattr("app.services.rag_service.embed", lambda text: None)
    RagService(db).add("Politique mots de passe", "Minimum 12 caractères, rotation 90 jours.")

    captured = {}

    def fake_chat_messages(self, messages):
        captured["system"] = messages[0]["content"]
        return "Réponse basée sur la doc."
    monkeypatch.setattr("app.services.ai_service.AIService._chat_messages", fake_chat_messages)

    r = client.post("/api/ai/chat", json={"question": "quelle est la politique de mots de passe ?", "history": []})
    assert r.status_code == 200
    # Le contenu du document a bien été injecté dans le prompt système.
    assert "12 caractères" in captured["system"]
    assert r.json()["sources"]  # sources renvoyées
