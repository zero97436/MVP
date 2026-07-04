from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Check(Base, TimestampMixin):
    __tablename__ = "checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(
        ForeignKey("hosts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    warning_threshold: Mapped[float | None] = mapped_column(Float)
    critical_threshold: Mapped[float | None] = mapped_column(Float)
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Sonde : si défini, le check est exécuté par l'AGENT de cet hôte (poller distant)
    # au lieu du serveur central. NULL = exécution centrale (par défaut).
    executor_host_id: Mapped[int | None] = mapped_column(
        ForeignKey("hosts.id", ondelete="SET NULL"), index=True
    )
    # Dernier statut connu (pour la détection de changement / alerting)
    last_status: Mapped[str | None] = mapped_column(String(16), index=True)

    host: Mapped["Host"] = relationship(  # noqa: F821
        back_populates="checks", foreign_keys=[host_id]
    )
    results: Mapped[list["CheckResult"]] = relationship(  # noqa: F821
        back_populates="check", cascade="all, delete-orphan"
    )
