"""Abstraction de notification : chaque canal implémente `send`."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Notification:
    subject: str
    body: str
    status: str
    check_name: str
    host_name: str


class Notifier(ABC):
    @abstractmethod
    def send(self, notification: Notification, config: dict) -> bool:  # pragma: no cover
        ...
