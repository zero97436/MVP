from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    check_id: Mapped[int] = mapped_column(
        ForeignKey("checks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(16))
    message: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Acquittement (un opérateur prend en charge l'incident sans le résoudre).
    acknowledged: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, nullable=False
    )
    acknowledged_by: Mapped[str | None] = mapped_column(String(255))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Horodatage d'escalade (une alerte n'est escaladée qu'une fois).
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
