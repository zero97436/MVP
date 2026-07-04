from sqlalchemy import Boolean, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class NotificationChannel(Base, TimestampMixin):
    __tablename__ = "notification_channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # email | webhook
    # config_json: pour email -> {"to": "..."} ; pour webhook -> {"url": "..."}
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Escalade : ce canal ne reçoit QUE les alertes escaladées (niveau astreinte).
    escalation_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Plage horaire d'activité "HH:MM-HH:MM" (vide = 24/7). Hors plage -> pas de notif.
    active_hours: Mapped[str | None] = mapped_column(String(16))
