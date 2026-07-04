from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentCommand(Base):
    """Commande à exécuter par l'agent sur un hôte (remédiation Niveau 2).

    Le backend ne peut demander que des ACTIONS NOMMÉES (jamais de commande shell
    libre) ; l'agent possède sa propre liste blanche et refuse tout le reste.
    Cycle : pending -> sent (récupérée par l'agent) -> done/failed.
    """

    __tablename__ = "agent_commands"

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(
        ForeignKey("hosts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    params: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    result: Mapped[str | None] = mapped_column(Text)
    requested_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
