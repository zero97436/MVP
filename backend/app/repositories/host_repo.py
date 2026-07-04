from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.host import Host


class HostRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[Host]:
        return list(self.db.scalars(select(Host).order_by(Host.name)))

    def get(self, host_id: int) -> Host | None:
        return self.db.get(Host, host_id)

    def create(self, **data) -> Host:
        host = Host(**data)
        self.db.add(host)
        self.db.commit()
        self.db.refresh(host)
        return host

    def update(self, host: Host, **data) -> Host:
        for key, value in data.items():
            setattr(host, key, value)
        self.db.commit()
        self.db.refresh(host)
        return host

    def delete(self, host: Host) -> None:
        self.db.delete(host)
        self.db.commit()
