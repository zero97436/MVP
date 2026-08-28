from sqlalchemy import JSON, Boolean, Float, ForeignKey, String, Text
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
    # Mode de supervision :
    #   agentless : le serveur sonde l'hôte directement sur le réseau (défaut).
    #   agent     : un agent installé sur l'hôte pousse ses métriques/résultats (HTTPS).
    #   ssh       : le serveur se connecte en SSH (tunnel) pour exécuter les checks.
    monitoring_mode: Mapped[str] = mapped_column(
        String(16), default="agentless", nullable=False, index=True
    )
    # Paramètres de connexion SSH réutilisés par les checks (mode ssh) :
    #   {port, user, password}. Le mot de passe est chiffré au repos (champ secret).
    ssh_config: Mapped[dict | None] = mapped_column(JSON)
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
