from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Ticket(Base, TimestampMixin):
    """Ticket ITSM lié (ou non) à un incident, poussé vers un outil externe.

    provider : internal | webhook | jira | servicenow
    status   : open | in_progress | resolved | closed
    """

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int | None] = mapped_column(
        ForeignKey("alerts.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="open", index=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    provider: Mapped[str] = mapped_column(String(16), default="internal", nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(128))
    external_url: Mapped[str | None] = mapped_column(String(512))
    created_by: Mapped[str | None] = mapped_column(String(255))
    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    assignee = relationship("User", foreign_keys=[assigned_to_id])
    tasks: Mapped[list["TicketTask"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", order_by="TicketTask.position"
    )
    comments: Mapped[list["TicketComment"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", order_by="TicketComment.created_at"
    )


class TicketTask(Base, TimestampMixin):
    """Tâche (checklist) à l'intérieur d'un ticket."""

    __tablename__ = "ticket_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    ticket: Mapped["Ticket"] = relationship(back_populates="tasks")


class TicketComment(Base, TimestampMixin):
    """Suivi (commentaire horodaté) d'un ticket — équivalent des suivis GLPI."""

    __tablename__ = "ticket_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    author: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, nullable=False)

    ticket: Mapped["Ticket"] = relationship(back_populates="comments")
