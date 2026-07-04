from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class HostMetric(Base):
    """Point de métrique système poussé par un agent de collecte distant.

    Une ligne = un échantillon horodaté pour un hôte (CPU/RAM/disque/réseau).
    """

    __tablename__ = "host_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(
        ForeignKey("hosts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    cpu_percent: Mapped[float | None] = mapped_column(Float)
    mem_percent: Mapped[float | None] = mapped_column(Float)
    disk_percent: Mapped[float | None] = mapped_column(Float)
    # Détail par disque : {"C:": 81.3, "D:": 1.6, ...}. disk_percent = le plus rempli.
    disks: Mapped[dict | None] = mapped_column(JSON)
    net_mbps: Mapped[float | None] = mapped_column(Float)
    process_count: Mapped[int | None] = mapped_column(Integer)
    load1: Mapped[float | None] = mapped_column(Float)        # charge système (1 min)
    temperature: Mapped[float | None] = mapped_column(Float)  # °C (capteur le plus chaud)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )

    host: Mapped["Host"] = relationship(back_populates="metrics")  # noqa: F821
