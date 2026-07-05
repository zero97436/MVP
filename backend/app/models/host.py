from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Host(Base, TimestampMixin):
    __tablename__ = "hosts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    hostname_or_ip: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    environment: Mapped[str] = mapped_column(String(64), default="production", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Dépendance : hôte parent (ex. switch/routeur en amont). Si le parent est en
    # panne, les alertes des enfants sont supprimées (injoignables, pas en panne).
    parent_host_id: Mapped[int | None] = mapped_column(
        ForeignKey("hosts.id", ondelete="SET NULL"), index=True
    )
    # Multi-tenant : tenant propriétaire (NULL = non assigné / partagé).
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"), index=True
    )
    # Vue géographique : site + coordonnées GPS (null = non placé sur la carte).
    location: Mapped[str | None] = mapped_column(String(255))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    checks: Mapped[list["Check"]] = relationship(  # noqa: F821
        back_populates="host", cascade="all, delete-orphan", foreign_keys="Check.host_id"
    )
    metrics: Mapped[list["HostMetric"]] = relationship(  # noqa: F821
        back_populates="host", cascade="all, delete-orphan"
    )
