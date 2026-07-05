from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    """Journal d'audit (Enterprise) : qui a fait quoi, quand, depuis où.

    Alimenté automatiquement par un middleware sur toutes les écritures API
    (POST/PUT/PATCH/DELETE) + les connexions. Conçu pour la conformité :
    enregistrements immuables (aucune API de modification/suppression unitaire).
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_email: Mapped[str | None] = mapped_column(String(255), index=True)
    method: Mapped[str] = mapped_column(String(8), nullable=False)
    path: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # ex. "hosts:create"
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    ip: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )
