from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MaintenanceWindow(Base):
    """Fenêtre de maintenance planifiée : pendant sa durée, les checks couverts
    n'ouvrent plus d'alertes (et ne notifient plus). Portée :
      - check_id défini  -> ce check uniquement
      - host_id défini   -> tous les checks de cet hôte
      - les deux NULL    -> global (toute la plateforme)
    """

    __tablename__ = "maintenance_windows"

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int | None] = mapped_column(
        ForeignKey("hosts.id", ondelete="CASCADE"), index=True
    )
    check_id: Mapped[int | None] = mapped_column(
        ForeignKey("checks.id", ondelete="CASCADE"), index=True
    )
    reason: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
