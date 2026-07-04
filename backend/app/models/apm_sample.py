from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ApmSample(Base):
    """Échantillon APM poussé par une application (fenêtre d'agrégation côté client).

    Chaque échantillon couvre une courte fenêtre (ex. 30-60 s) :
      - requests   : nombre de requêtes traitées sur la fenêtre
      - errors     : dont erreurs (HTTP 5xx, exceptions…)
      - latency_ms : latence moyenne des requêtes de la fenêtre (ms)
    """

    __tablename__ = "apm_samples"

    id: Mapped[int] = mapped_column(primary_key=True)
    app_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    environment: Mapped[str] = mapped_column(String(64), default="prod", nullable=False)
    requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[float | None] = mapped_column(Float)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )
