from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class KnowledgeDocument(Base, TimestampMixin):
    """Document de la base de connaissances (RAG) : runbook, procédure, note.

    embedding : vecteur (liste de floats) calculé via Ollama, pour la recherche
    sémantique. Null si le modèle d'embeddings n'était pas disponible — la
    recherche bascule alors sur un score par mots-clés.
    """

    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255))
    embedding: Mapped[list | None] = mapped_column(JSON)
