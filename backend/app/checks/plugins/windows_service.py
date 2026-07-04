"""Check windows_service : état d'un service Windows.

S'exécute par l'AGENT installé sur l'hôte Windows (champ « Exécuté par »), qui lit
l'état du service via psutil. Le serveur central ne peut pas l'exécuter directement.

config_json : {"service": "Spooler"}   (nom court du service)
"""
from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus


class WindowsServiceCheck(BaseCheck):
    type = "windows_service"

    def run(self, ctx: CheckContext) -> CheckResultData:
        return CheckResultData(
            status=CheckStatus.UNKNOWN,
            message="Ce check doit être exécuté par l'agent de l'hôte Windows "
                    "(définir « Exécuté par » sur cet hôte).",
        )
