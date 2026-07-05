"""Base de connaissances (RAG) : runbooks/procédures pour l'assistant IA."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_operator
from app.db.session import get_db
from app.services.rag_service import RagService

router = APIRouter(prefix="/knowledge", tags=["knowledge"], dependencies=[Depends(get_current_user)])


def _out(d) -> dict:
    return {
        "id": d.id, "title": d.title, "source": d.source,
        "chars": len(d.content or ""),
        "embedded": bool(d.embedding),
        "content": d.content,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


class DocIn(BaseModel):
    title: str
    content: str
    source: str | None = None


class SearchIn(BaseModel):
    query: str


class ImportIn(BaseModel):
    documents: list[DocIn] | None = None   # import de fichiers / liste
    markdown: str | None = None            # gros document découpé par titres
    source: str | None = None


@router.get("")
def list_docs(db: Session = Depends(get_db)):
    return [_out(d) for d in RagService(db).list()]


@router.post("", status_code=201, dependencies=[Depends(require_operator)])
def add_doc(payload: DocIn, db: Session = Depends(get_db)):
    if not payload.title.strip() or not payload.content.strip():
        raise HTTPException(400, "title et content requis")
    return _out(RagService(db).add(payload.title.strip(), payload.content, payload.source))


@router.delete("/{doc_id}", status_code=204, dependencies=[Depends(require_operator)])
def delete_doc(doc_id: int, db: Session = Depends(get_db)):
    if not RagService(db).delete(doc_id):
        raise HTTPException(404, "Document introuvable")


@router.post("/import", dependencies=[Depends(require_operator)])
def import_docs(payload: ImportIn, db: Session = Depends(get_db)):
    """Import en lot : liste de documents et/ou gros Markdown découpé par titres."""
    from app.services.rag_service import split_markdown

    svc = RagService(db)
    docs: list[dict] = [d.model_dump() for d in (payload.documents or [])]
    if payload.markdown and payload.markdown.strip():
        docs += split_markdown(payload.markdown, payload.source)
    if not docs:
        raise HTTPException(400, "Aucun document à importer (documents ou markdown requis)")
    return {"imported": svc.import_many(docs)}


@router.post("/starter-pack", dependencies=[Depends(require_operator)])
def starter_pack(db: Session = Depends(get_db)):
    """Insère une base de problèmes IT courants (Windows, Office, réseau, matériel)."""
    return {"imported": RagService(db).import_starter_pack()}


@router.post("/reindex", dependencies=[Depends(require_operator)])
def reindex(db: Session = Depends(get_db)):
    """Recalcule les embeddings (après un `ollama pull nomic-embed-text`)."""
    return {"embedded": RagService(db).reindex()}


@router.post("/search")
def search(payload: SearchIn, db: Session = Depends(get_db)):
    """Aperçu de ce que le RAG récupérerait pour une question (debug/démo)."""
    hits = RagService(db).search(payload.query)
    return [{"id": d.id, "title": d.title, "score": round(s, 3)} for d, s in hits]
