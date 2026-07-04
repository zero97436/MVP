from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CheckTemplate(Base, TimestampMixin):
    """Modèle de checks : jeu de checks standard applicable à un hôte en un clic.

    items : liste de définitions de checks, ex.
      [{"name": "Ping", "type": "ping", "config_json": {}, "interval_seconds": 60,
        "timeout_seconds": 5, "warning_threshold": null, "critical_threshold": null}]
    """

    __tablename__ = "check_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    items: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
