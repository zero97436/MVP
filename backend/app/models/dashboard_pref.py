from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class DashboardPref(Base, TimestampMixin):
    """Préférences de dashboard par utilisateur (ordre + visibilité des sections)."""

    __tablename__ = "dashboard_prefs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    # [{"id": "hero", "visible": true}, ...] — ordre de la liste = ordre d'affichage.
    layout: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
