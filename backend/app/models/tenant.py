from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    """Client (tenant) d'un déploiement MSP multi-tenant (Business/Enterprise).

    Les utilisateurs et hôtes rattachés à un tenant sont cloisonnés : un
    utilisateur d'un tenant ne voit que les données de son tenant. Les
    utilisateurs SANS tenant (tenant_id NULL) sont le personnel MSP « global »
    et voient l'ensemble des tenants.
    """

    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
