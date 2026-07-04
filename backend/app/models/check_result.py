from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CheckResult(Base):
    __tablename__ = "check_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    check_id: Mapped[int] = mapped_column(
        ForeignKey("checks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    message: Mapped[str | None] = mapped_column(Text)
    perfdata: Mapped[dict] = mapped_column(JSON, default=dict)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )

    check: Mapped["Check"] = relationship(back_populates="results")  # noqa: F821
