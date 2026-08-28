from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Role(Base, TimestampMixin):
    """Rôle personnalisé : liste des sections où la modification est autorisée."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    # Liste de sections (voir app.core.rbac.SECTIONS) où l'écriture est permise.
    permissions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
