from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HostMetricHourly(Base):
    """Agrégat horaire (downsampling) des métriques d'un hôte.

    Une ligne = un hôte × une heure, avec moyenne et max de chaque métrique.
    Conservé bien plus longtemps que les échantillons bruts (host_metrics),
    ce qui permet des tendances long terme sans faire grossir la base.
    """

    __tablename__ = "host_metrics_hourly"

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(
        ForeignKey("hosts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    bucket: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    cpu_avg: Mapped[float | None] = mapped_column(Float)
    cpu_max: Mapped[float | None] = mapped_column(Float)
    mem_avg: Mapped[float | None] = mapped_column(Float)
    mem_max: Mapped[float | None] = mapped_column(Float)
    disk_avg: Mapped[float | None] = mapped_column(Float)
    disk_max: Mapped[float | None] = mapped_column(Float)
    net_avg: Mapped[float | None] = mapped_column(Float)
    net_max: Mapped[float | None] = mapped_column(Float)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
