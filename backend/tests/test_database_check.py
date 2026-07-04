import os

import pytest

from app.checks.base import CheckContext
from app.checks.plugins.database import DatabaseCheck


def _ctx(host, config, timeout=3):
    return CheckContext(
        hostname_or_ip=host, timeout_seconds=timeout,
        warning_threshold=None, critical_threshold=None, config=config,
    )


def test_unknown_engine_is_unknown():
    res = DatabaseCheck().run(_ctx("db", {"engine": "mongodb"}))
    assert res.status.value == "UNKNOWN"


def test_postgres_unreachable_is_critical():
    res = DatabaseCheck().run(_ctx("10.255.255.20", {"engine": "postgresql"}, timeout=1))
    assert res.status.value == "CRITICAL"


def test_oracle_unreachable_is_critical():
    res = DatabaseCheck().run(_ctx("10.255.255.21", {"engine": "oracle"}, timeout=1))
    assert res.status.value == "CRITICAL"


def test_mssql_unreachable_is_critical():
    res = DatabaseCheck().run(_ctx("10.255.255.22", {"engine": "mssql"}, timeout=1))
    assert res.status.value == "CRITICAL"


@pytest.mark.skipif(
    "db" not in os.environ.get("DATABASE_URL", ""),
    reason="Postgres de la stack non disponible (tests hors conteneur)",
)
def test_postgres_real_connection_ok():
    res = DatabaseCheck().run(_ctx("db", {
        "engine": "postgresql", "port": 5432,
        "user": "supervision", "password": "supervision", "dbname": "supervision",
    }))
    assert res.status.value == "OK"
    assert res.value is not None
