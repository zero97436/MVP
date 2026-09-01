import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_lang
from app.core.config import settings
from app.core.logging import get_logger
from app.core.ratelimit import login_limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, Token, UserOut

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
RESET_TTL_MINUTES = 30


class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=128)


class ForgotPassword(BaseModel):
    email: str  # accepte aussi les e-mails internes (ex. admin@local)


class ResetPassword(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=128)


def _pw_fingerprint(user: User) -> str:
    """Empreinte du mot de passe actuel : rend le lien à USAGE UNIQUE
    (il devient invalide dès que le mot de passe change)."""
    return hashlib.sha256(user.hashed_password.encode()).hexdigest()[:16]


def _make_reset_token(user: User) -> str:
    return jwt.encode(
        {
            "sub": user.email,
            "purpose": "pwreset",
            "fp": _pw_fingerprint(user),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=RESET_TTL_MINUTES),
        },
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )


def _reset_link(request: Request, token: str) -> str:
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{proto}://{host}/reset-password?token={token}"


def _send_reset_email(to: str, link: str, lang: str = "fr") -> bool:
    if not settings.SMTP_HOST:
        return False
    import smtplib
    from email.mime.text import MIMEText

    if lang == "en":
        body = (
            "Hello,\n\nYou requested a reset of your Opsora password.\n\n"
            f"Click this link (valid for {RESET_TTL_MINUTES} minutes):\n{link}\n\n"
            "If you did not request this, ignore this email.\n\nThe Opsora team"
        )
        subject = "Reset your Opsora password"
    else:
        body = (
            "Bonjour,\n\nVous avez demandé la réinitialisation de votre mot de passe Opsora.\n\n"
            f"Cliquez sur ce lien (valable {RESET_TTL_MINUTES} minutes) :\n{link}\n\n"
            "Si vous n'êtes pas à l'origine de cette demande, ignorez cet e-mail.\n\nL'équipe Opsora"
        )
        subject = "Réinitialisation de votre mot de passe Opsora"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
            if settings.SMTP_TLS:
                s.starttls()
            if settings.SMTP_USER:
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.send_message(msg)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Envoi e-mail de réinitialisation échoué : %s", exc)
        return False


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


@router.post("/change-password")
def change_password(
    payload: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Un utilisateur change SON propre mot de passe (vérifie l'actuel)."""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    if payload.new_password == payload.current_password:
        raise HTTPException(status_code=400, detail="Le nouveau mot de passe doit être différent")
    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"ok": True}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPassword, request: Request, db: Session = Depends(get_db),
                    lang: str = Depends(get_lang)):
    """Envoie un lien de réinitialisation. Réponse toujours neutre (anti-énumération)."""
    user = UserRepository(db).get_by_email(payload.email)
    if user and user.is_active:
        link = _reset_link(request, _make_reset_token(user))
        if not _send_reset_email(user.email, link, lang):
            # SMTP non configuré : on journalise le lien (dev / diagnostic).
            logger.info("Lien de réinitialisation pour %s : %s", user.email, link)
    # Ne révèle jamais si l'e-mail existe. Message neutre localisé côté client.
    msg = ("If an account exists, a reset email has been sent." if lang == "en"
           else "Si un compte existe, un e-mail de réinitialisation a été envoyé.")
    return {"ok": True, "message": msg}


@router.post("/reset-password")
def reset_password(payload: ResetPassword, db: Session = Depends(get_db)):
    """Applique le nouveau mot de passe à partir d'un lien valide (usage unique)."""
    try:
        data = jwt.decode(payload.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(400, "Lien invalide ou expiré")
    if data.get("purpose") != "pwreset":
        raise HTTPException(400, "Lien invalide")
    user = UserRepository(db).get_by_email(data.get("sub", ""))
    if not user or not user.is_active:
        raise HTTPException(400, "Lien invalide")
    # Usage unique : l'empreinte doit correspondre au mot de passe actuel.
    if data.get("fp") != _pw_fingerprint(user):
        raise HTTPException(400, "Lien déjà utilisé ou expiré")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    logger.info("Mot de passe réinitialisé pour %s", user.email)
    return {"ok": True}
