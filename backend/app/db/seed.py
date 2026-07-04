"""Seed initial : admin + hôtes/checks de démonstration.

Lancement : python -m app.db.seed
Idempotent : ne recrée pas ce qui existe déjà.
"""
import math
import random
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.check import Check
from app.models.host import Host
from app.models.host_metric import HostMetric
from app.models.user import User
from app.repositories.user_repo import UserRepository

logger = get_logger("seed")


def seed() -> None:
    db = SessionLocal()
    try:
        # --- Admin ---
        if not UserRepository(db).get_by_email(settings.ADMIN_EMAIL):
            db.add(
                User(
                    email=settings.ADMIN_EMAIL,
                    hashed_password=hash_password(settings.ADMIN_PASSWORD),
                    full_name="Administrator",
                    is_admin=True,
                    is_active=True,
                    role="admin",
                )
            )
            db.commit()
            logger.info("Admin user created: %s", settings.ADMIN_EMAIL)

        # --- Hôtes de démo ---
        if db.query(Host).count() == 0:
            h1 = Host(
                name="localhost",
                hostname_or_ip="127.0.0.1",
                description="Local machine",
                environment="dev",
            )
            h2 = Host(
                name="example.com",
                hostname_or_ip="example.com",
                description="Public website",
                environment="production",
            )
            db.add_all([h1, h2])
            db.commit()

            db.add_all(
                [
                    Check(host_id=h1.id, name="Ping local", type="ping",
                          interval_seconds=60, timeout_seconds=5),
                    Check(host_id=h2.id, name="HTTP example", type="http",
                          interval_seconds=120, timeout_seconds=10,
                          warning_threshold=800, critical_threshold=2000,
                          config_json={"url": "https://example.com", "expected_status": 200}),
                    Check(host_id=h2.id, name="SSL example", type="ssl_expiry",
                          interval_seconds=3600, timeout_seconds=10,
                          warning_threshold=30, critical_threshold=7,
                          config_json={"port": 443}),
                    Check(host_id=h1.id, name="Disk (mock)", type="disk_usage",
                          interval_seconds=300, warning_threshold=80, critical_threshold=90,
                          config_json={"mock": True}),
                ]
            )
            db.commit()
            logger.info("Demo hosts and checks created")

        # --- Métriques de démo (24h) pour alimenter les widgets ressources ---
        if db.query(HostMetric).count() == 0:
            _seed_metrics(db)
            logger.info("Demo host metrics created")
    finally:
        db.close()


def _seed_metrics(db) -> None:
    """Génère 24h de points (1 / 30 min) par hôte. Données de démonstration
    réalistes en attendant un vrai agent de collecte."""
    now = datetime.now(timezone.utc)
    points = 48
    metrics: list[HostMetric] = []
    for host in db.query(Host).all():
        cpu_base = random.uniform(20, 45)
        mem_base = random.uniform(45, 65)
        disk_base = random.uniform(55, 70)
        for i in range(points):
            ts = now - timedelta(minutes=30 * (points - 1 - i))
            wave = math.sin(i / 5 + host.id)
            disk_main = round(_clamp(disk_base + i * 0.05 + random.uniform(-1, 1)), 1)
            disks = {
                "C:": disk_main,
                "D:": round(_clamp(15 + random.uniform(-2, 2)), 1),
            }
            metrics.append(
                HostMetric(
                    host_id=host.id,
                    cpu_percent=round(_clamp(cpu_base + wave * 18 + random.uniform(-6, 6)), 1),
                    mem_percent=round(_clamp(mem_base + wave * 10 + random.uniform(-4, 4)), 1),
                    disk_percent=disk_main,
                    disks=disks,
                    net_mbps=round(max(0.0, 80 + wave * 40 + random.uniform(-20, 20)), 1),
                    collected_at=ts,
                )
            )
    db.add_all(metrics)
    db.commit()


def _clamp(v: float, lo: float = 1.0, hi: float = 99.0) -> float:
    return max(lo, min(hi, v))


if __name__ == "__main__":
    seed()
