"""Check `ntp` : interroge un serveur NTP et mesure la dérive d'horloge (offset).

Seuils warning/critical du check = dérive absolue en millisecondes
(défauts : 100 ms / 1000 ms).

config_json :
  - port : port NTP (défaut 123)
"""
import socket
import struct
import time

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus

NTP_EPOCH = 2208988800  # 1900-01-01 -> 1970-01-01


def _query_ntp(host: str, port: int, timeout: int) -> tuple[float, float]:
    """Renvoie (offset_ms, rtt_ms). Isolé pour être mockable en test."""
    packet = b"\x1b" + 47 * b"\x00"  # SNTP v3, mode client
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(timeout)
        t0 = time.time()
        s.sendto(packet, (host, port))
        data, _ = s.recvfrom(48)
        t3 = time.time()
    if len(data) < 48:
        raise ValueError("réponse NTP tronquée")
    secs, frac = struct.unpack("!II", data[40:48])  # Transmit Timestamp
    server_time = secs - NTP_EPOCH + frac / 2**32
    offset = server_time - (t0 + t3) / 2
    return offset * 1000, (t3 - t0) * 1000


class NtpCheck(BaseCheck):
    type = "ntp"

    def run(self, ctx: CheckContext) -> CheckResultData:
        port = int(ctx.config.get("port", 123))
        try:
            offset_ms, rtt_ms = _query_ntp(ctx.hostname_or_ip, port, ctx.timeout_seconds)
        except Exception as exc:  # noqa: BLE001
            return CheckResultData(
                status=CheckStatus.CRITICAL,
                message=f"Serveur NTP injoignable : {str(exc)[:100]}",
            )

        warn = ctx.warning_threshold if ctx.warning_threshold is not None else 100
        crit = ctx.critical_threshold if ctx.critical_threshold is not None else 1000
        drift = abs(offset_ms)
        if drift >= crit:
            status = CheckStatus.CRITICAL
        elif drift >= warn:
            status = CheckStatus.WARNING
        else:
            status = CheckStatus.OK
        return CheckResultData(
            status=status,
            value=round(offset_ms, 1),
            message=f"Dérive {offset_ms:+.1f} ms (RTT {rtt_ms:.0f} ms) — warn {warn} ms / crit {crit} ms",
            perfdata={"offset_ms": round(offset_ms, 1), "rtt_ms": round(rtt_ms, 1)},
        )
