"""Dépendances FastAPI partagées (auth)."""
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise credentials_error
    user = UserRepository(db).get_by_email(payload["sub"])
    if not user or not user.is_active:
        raise credentials_error
    return user


def require_roles(*roles: str):
    """Fabrique une dépendance qui exige l'un des rôles donnés."""

    allowed = set(roles)

    def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle insuffisant (requis : {', '.join(sorted(allowed))})",
            )
        return user

    return _dep


# Raccourcis : admin seul, ou opérateur+admin (actions de modification).
require_admin = require_roles("admin")
require_operator = require_roles("admin", "operator")


def require_ingest_key(x_ingest_key: str | None = Header(default=None)) -> None:
    """Auth des agents par clé API (en-tête X-Ingest-Key). Vide = ouvert (dev)."""
    expected = settings.INGEST_API_KEY
    if expected and x_ingest_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Ingest-Key",
        )
