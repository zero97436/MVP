"""Helpers SNMP partagés (snmpget multi-OID, découverte d'interfaces)."""
import subprocess


def snmpget(host: str, community: str, version: str, oids: list[str], timeout: int) -> list[str]:
    """Renvoie les valeurs (ordre des OIDs). Lève RuntimeError si échec."""
    cmd = ["snmpget", "-v", version, "-c", community, "-Oqv",
           "-t", str(max(1, timeout)), "-r", "1", host, *oids]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * 2 + 5)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip().splitlines()
        raise RuntimeError(err[-1] if err else "snmpget a échoué")
    return [line.strip().strip('"') for line in proc.stdout.strip().splitlines()]


def list_interfaces(host: str, community: str, version: str, timeout: int) -> list[dict]:
    """Découvre les interfaces (index + nom) via IF-MIB::ifDescr."""
    cmd = ["snmpwalk", "-v", version, "-c", community, "-Oqn",
           "-t", str(max(1, timeout)), "-r", "1", host, "1.3.6.1.2.1.2.2.1.2"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * 3 + 5)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip().splitlines()
        raise RuntimeError(err[-1] if err else "snmpwalk a échoué")
    out = []
    for line in proc.stdout.strip().splitlines():
        # Format -Oqn : ".1.3.6.1.2.1.2.2.1.2.<index> <nom>"
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        oid, name = parts
        index = oid.rsplit(".", 1)[-1]
        out.append({"index": int(index) if index.isdigit() else index, "name": name.strip('"')})
    return out
