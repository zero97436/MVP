from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from typing import Any

from app.api.deps import get_current_user, require_operator
from app.db.session import get_db
from app.services.ai_service import AIService, OllamaError

router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[Depends(get_current_user)])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list)


class ApplyPlanRequest(BaseModel):
    operations: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/chat")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """Assistant NL : répond à partir de l'état courant de la plateforme."""
    try:
        return AIService(db).chat(
            payload.question, [m.model_dump() for m in payload.history]
        )
    except OllamaError as exc:
        raise HTTPException(503, str(exc))


@router.post("/apply-plan", dependencies=[Depends(require_operator)])
def apply_plan(payload: ApplyPlanRequest, db: Session = Depends(get_db)):
    """Crée l'hôte + checks proposés par l'assistant (validé par un opérateur)."""
    try:
        return AIService(db).apply_plan(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(400, str(exc))
