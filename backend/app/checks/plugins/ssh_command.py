"""Check ssh_command (façon check_by_ssh) : exécute une commande via SSH et évalue
le résultat. Permet d'utiliser un équipement comme point d'exécution (ex. lancer
'/ping' sur un MikroTik), ou de vérifier l'état d'un service sur un serveur.

config_json :
  - user, password : identifiants SSH
  - port           : port SSH (défaut 22)
  - command        : commande à exécuter (obligatoire)
  - expect         : sous-chaîne attendue dans la sortie (optionnel) -> OK si présente

⚠️ Le mot de passe est stocké dans config_json — usage interne, compte SSH dédié recommandé.
"""
import time

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus


class SshCommandCheck(BaseCheck):
    type = "ssh_command"

    def run(self, ctx: CheckContext) -> CheckResultData:
        cfg = ctx.config
        command = cfg.get("command")
        if not command:
            return CheckResultData(status=CheckStatus.UNKNOWN, message="'command' manquante")

        try:
            import paramiko
        except ImportError:
            return CheckResultData(status=CheckStatus.UNKNOWN, message="paramiko non installé")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        t0 = time.time()
        try:
            client.connect(
                ctx.hostname_or_ip,
                port=int(cfg.get("port", 22)),
                username=cfg.get("user", ""),
                password=cfg.get("password", ""),
                timeout=ctx.timeout_seconds,
                banner_timeout=ctx.timeout_seconds,
                auth_timeout=ctx.timeout_seconds,
                look_for_keys=False,
                allow_agent=False,
            )
            stdin, stdout, stderr = client.exec_command(command, timeout=ctx.timeout_seconds)
            output = stdout.read().decode(errors="replace")
            err = stderr.read().decode(errors="replace")
            code = stdout.channel.recv_exit_status()
        except Exception as exc:  # noqa: BLE001
            return CheckResultData(
                status=CheckStatus.CRITICAL, message=f"SSH échoué : {str(exc)[:120]}"
            )
        finally:
            client.close()

        ms = int((time.time() - t0) * 1000)
        combined = (output + err).strip()
        expect = cfg.get("expect")

        if expect:
            ok = expect in combined
        else:
            ok = code == 0
        status = CheckStatus.OK if ok else CheckStatus.CRITICAL
        snippet = combined.replace("\n", " ")[:120] or f"exit={code}"
        return CheckResultData(
            status=status,
            value=float(ms),
            message=f"{'OK' if ok else 'ÉCHEC'} (exit={code}) : {snippet}",
            perfdata={"exit_code": code, "duration_ms": ms},
        )
