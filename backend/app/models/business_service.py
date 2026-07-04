from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BusinessService(Base):
    """Service métier : agrégat de composants (checks/hôtes) avec une règle d'impact.

    rule :
      - 'worst'   : statut = le pire des composants (une panne impacte le service)
      - 'percent' : basé sur le % de composants OK (seuils warning/critical en %)
    """

    __tablename__ = "business_services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    rule: Mapped[str] = mapped_column(String(16), default="worst", nullable=False)
    warning_threshold: Mapped[float | None] = mapped_column(Float)   # % (rule percent)
    critical_threshold: Mapped[float | None] = mapped_column(Float)
    # Vue Opérations : couche d'affichage + icône de la tuile.
    category: Mapped[str] = mapped_column(String(64), default="Général", nullable=False, server_default="Général")
    icon: Mapped[str | None] = mapped_column(String(32))
    # Position libre sur la carte (drag & drop) ; null = placement auto par couche.
    pos_x: Mapped[int | None] = mapped_column(Integer)
    pos_y: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    components: Mapped[list["BusinessServiceComponent"]] = relationship(  # noqa: F821
        back_populates="service", cascade="all, delete-orphan"
    )


class BusinessServiceComponent(Base):
    """Composant d'un service métier : référence un check OU un hôte."""

    __tablename__ = "business_service_components"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_service_id: Mapped[int] = mapped_column(
        ForeignKey("business_services.id", ondelete="CASCADE"), index=True, nullable=False
    )
    check_id: Mapped[int | None] = mapped_column(ForeignKey("checks.id", ondelete="CASCADE"))
    host_id: Mapped[int | None] = mapped_column(ForeignKey("hosts.id", ondelete="CASCADE"))
    label: Mapped[str | None] = mapped_column(String(255))

    service: Mapped["BusinessService"] = relationship(back_populates="components")  # noqa: F821
