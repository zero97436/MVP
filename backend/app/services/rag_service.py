"""RAG : base de connaissances + récupération de passages pertinents.

Embeddings via Ollama (100 % local). Recherche par similarité cosinus si les
embeddings sont disponibles, sinon repli sur un score par mots-clés — le RAG
fonctionne donc même sans le modèle d'embeddings installé (en mode dégradé).
"""
from __future__ import annotations

import math
import re

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.knowledge import KnowledgeDocument

logger = get_logger(__name__)

_WORD_RE = re.compile(r"[a-zàâäéèêëîïôöùûüç0-9]{3,}", re.IGNORECASE)
_STOP = {"les", "des", "une", "pour", "avec", "sur", "dans", "est", "que", "qui",
         "the", "and", "for", "with", "this", "that", "sont", "par", "aux"}


def embed(text: str) -> list[float] | None:
    """Vecteur d'embedding via Ollama. None si indisponible (repli mots-clés)."""
    try:
        r = httpx.post(
            f"{settings.OLLAMA_BASE_URL}/api/embeddings",
            json={"model": settings.OLLAMA_EMBED_MODEL, "prompt": text[:8000]},
            timeout=30,
        )
        r.raise_for_status()
        vec = r.json().get("embedding")
        return vec if isinstance(vec, list) and vec else None
    except Exception as exc:  # noqa: BLE001
        logger.debug("Embedding indisponible (%s) -> repli mots-clés", exc)
        return None


def split_markdown(text: str, source: str | None = None) -> list[dict]:
    """Découpe un document en sections sur les titres Markdown (# / ##).

    Chaque section (titre + contenu jusqu'au titre suivant) devient un document —
    granularité idéale pour la récupération RAG. Sans titre, renvoie un seul doc.
    """
    lines = text.splitlines()
    docs: list[dict] = []
    title, buf = None, []

    def flush():
        if title and "".join(buf).strip():
            docs.append({"title": title[:255], "content": "\n".join(buf).strip(), "source": source})

    for line in lines:
        m = re.match(r"^#{1,3}\s+(.+?)\s*#*\s*$", line)
        if m:
            flush()
            title, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    flush()

    if not docs:  # aucun titre -> document unique
        body = text.strip()
        if body:
            first = body.splitlines()[0][:80]
            docs.append({"title": (source or first)[:255], "content": body, "source": source})
    return docs


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _keywords(text: str) -> set[str]:
    return {w.lower() for w in _WORD_RE.findall(text)} - _STOP


class RagService:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[KnowledgeDocument]:
        return list(self.db.scalars(select(KnowledgeDocument).order_by(KnowledgeDocument.title)))

    def add(self, title: str, content: str, source: str | None = None) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            title=title[:255], content=content, source=(source or None),
            embedding=embed(f"{title}\n{content}"),
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def delete(self, doc_id: int) -> bool:
        doc = self.db.get(KnowledgeDocument, doc_id)
        if not doc:
            return False
        self.db.delete(doc)
        self.db.commit()
        return True

    def import_many(self, documents: list[dict]) -> int:
        """Ajoute plusieurs documents d'un coup (import de fichiers / collage)."""
        n = 0
        for d in documents:
            title = (d.get("title") or "").strip()
            content = (d.get("content") or "").strip()
            if not title or not content:
                continue
            self.db.add(KnowledgeDocument(
                title=title[:255], content=content, source=(d.get("source") or None),
                embedding=embed(f"{title}\n{content}"),
            ))
            n += 1
        if n:
            self.db.commit()
        return n

    def import_starter_pack(self) -> int:
        """Insère une base de problèmes IT courants (Windows, Office, réseau…)."""
        from app.services.knowledge_seed import STARTER_PACK

        existing = {d.title for d in self.list()}
        fresh = [d for d in STARTER_PACK if d["title"] not in existing]
        return self.import_many(fresh)

    def reindex(self) -> int:
        """Recalcule les embeddings de tous les documents (après pull du modèle)."""
        docs = self.list()
        n = 0
        for doc in docs:
            vec = embed(f"{doc.title}\n{doc.content}")
            if vec:
                doc.embedding = vec
                n += 1
        self.db.commit()
        return n

    def search(self, query: str, k: int | None = None) -> list[tuple[KnowledgeDocument, float]]:
        docs = self.list()
        if not docs:
            return []
        k = k or settings.RAG_TOP_K
        qvec = embed(query)
        scored: list[tuple[KnowledgeDocument, float]] = []
        if qvec and any(d.embedding for d in docs):
            for d in docs:
                if d.embedding:
                    scored.append((d, _cosine(qvec, d.embedding)))
        else:
            # Repli mots-clés (Jaccard pondéré par recouvrement de la requête).
            qwords = _keywords(query)
            for d in docs:
                dwords = _keywords(f"{d.title} {d.content}")
                inter = len(qwords & dwords)
                scored.append((d, inter / len(qwords) if qwords else 0.0))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [(d, s) for d, s in scored[:k] if s > 0]

    def context_for(self, query: str) -> tuple[str, list[dict]]:
        """Renvoie (bloc de contexte à injecter, liste des sources citées)."""
        hits = self.search(query)
        if not hits:
            return "", []
        blocks, sources = [], []
        for doc, score in hits:
            blocks.append(f"### {doc.title}\n{doc.content[:1500]}")
            sources.append({"id": doc.id, "title": doc.title, "score": round(score, 3)})
        return "\n\n".join(blocks), sources
