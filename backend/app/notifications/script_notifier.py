"""Notifier « script perso » (event handler) : exécute une commande sur alerte.

config_json : {"command": "/opt/scripts/handler.sh"}
Les détails de l'alerte sont passés en variables d'environnement :
  SUPERVISION_STATUS, SUPERVISION_HOST, SUPERVISION_CHECK, SUPERVISION_MESSAGE

⚠️ Puissant : la commande s'exécute côté backend. Réservé aux administrateurs
(création de canaux = admin) ; à utiliser en connaissance de cause.
"""
import subprocess

from app.core.logging import get_logger
from app.notifications.base import Notification, Notifier

logger = get_logger(__name__)


class ScriptNotifier(Notifier):
    def send(self, notification: Notification, config: dict) -> bool:
        command = config.get("command")
        if not command:
            logger.warning("ScriptNotifier: 'command' manquante")
            return False
        env = {
            "SUPERVISION_STATUS": notification.status,
            "SUPERVISION_HOST": notification.host_name,
            "SUPERVISION_CHECK": notification.check_name,
            "SUPERVISION_MESSAGE": notification.body or "",
        }
        try:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=20,
                env={**__import__("os").environ, **env},
            )
            if proc.returncode == 0:
                logger.info("Script handler exécuté (rc=0)")
                return True
            logger.error("Script handler rc=%s : %s", proc.returncode, (proc.stderr or "")[:120])
            return False
        except Exception as exc:  # noqa: BLE001
            logger.error("ScriptNotifier failed: %s", exc)
            return False
