from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RemediationLog(Base):
    """Journal d'audit des actions de remédiation déclenchées sur un incident.

    Chaque exécution (validée par un humain) est tracée : action, résultat, auteur.
    """

    __tablename__ = "remediation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int | None] = mapped_column(
        ForeignKey("alerts.id", ondelete="SET NULL"), index=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)  # success | failed
    detail: Mapped[str | None] = mapped_column(Text)
    params: Mapped[dict | None] = mapped_column(JSON)
    performed_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
