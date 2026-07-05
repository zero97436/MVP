from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Branding(Base, TimestampMixin):
    """Personnalisation de marque (plan Professional) — une seule ligne (id=1).

    logo_url : URL http(s) ou data-URL (image encodée) ; vide = logo Opsora.
    """

    __tablename__ = "branding"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(64))
    tagline: Mapped[str | None] = mapped_column(String(128))
    logo_url: Mapped[str | None] = mapped_column(Text)
    accent_color: Mapped[str | None] = mapped_column(String(16))  # ex. #7C3AED
