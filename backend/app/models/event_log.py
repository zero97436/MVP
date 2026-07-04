from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EventLog(Base):
    """Journal global des événements : alertes, acquittements, maintenances,
    remédiations, actions utilisateurs… pour un historique consultable et filtrable.
    """

    __tablename__ = "event_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(48), index=True, nullable=False)
    level: Mapped[str] = mapped_column(String(16), default="info", nullable=False)  # info|warning|critical
    message: Mapped[str] = mapped_column(Text, nullable=False)
    host_id: Mapped[int | None] = mapped_column(Integer, index=True)
    check_id: Mapped[int | None] = mapped_column(Integer, index=True)
    actor: Mapped[str | None] = mapped_column(String(255))  # email ou "system"
    meta: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )
