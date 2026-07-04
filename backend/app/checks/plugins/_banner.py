"""Helper commun : connexion TCP + lecture de la bannière du service."""
import socket
import time


def grab_banner(host: str, port: int, timeout: int) -> tuple[str, int]:
    """Ouvre une connexion TCP, lit la bannière et renvoie (texte, durée_ms)."""
    t0 = time.time()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        try:
            data = sock.recv(256)
        except socket.timeout:
            data = b""
    ms = int((time.time() - t0) * 1000)
    return data.decode(errors="replace").strip(), ms
