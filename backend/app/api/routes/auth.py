from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.ratelimit import login_limiter
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, Token, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Login JSON : {email, password} -> {access_token}. Anti-bruteforce par IP."""
    # Derrière nginx, l'IP réelle est dans X-Forwarded-For (1ère valeur).
    fwd = request.headers.get("x-forwarded-for")
    client_ip = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "unknown")
    if login_limiter.is_blocked(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de tentatives. Réessayez plus tard.",
        )

    user = UserRepository(db).get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        login_limiter.record_failure(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    login_limiter.reset(client_ip)  # succès -> on remet le compteur à zéro
    token = create_access_token(subject=user.email)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
