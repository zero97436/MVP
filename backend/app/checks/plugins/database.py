"""Check database : connexion à une base + requête + temps de réponse.

Compatible PostgreSQL (psycopg2), MySQL/MariaDB (pymysql), Oracle (oracledb, mode
thin) et Microsoft SQL Server (pymssql).

config_json :
  - engine   : "postgresql" | "mysql" | "oracle" | "mssql"
               (alias: postgres/pg, mariadb, sqlserver) — défaut postgresql
  - port     : port (défaut 5432 pg / 3306 mysql / 1521 oracle / 1433 mssql)
  - user, password, dbname (service_name pour Oracle)
  - query    : requête de test (défaut "SELECT 1")

Seuils (warning_threshold / critical_threshold) appliqués au temps de réponse (ms).
⚠️ Le mot de passe est stocké dans config_json — réservé à un usage interne.
"""
import time

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus

PG_ALIASES = {"postgresql", "postgres", "pg"}
MYSQL_ALIASES = {"mysql", "mariadb"}
ORACLE_ALIASES = {"oracle"}
MSSQL_ALIASES = {"mssql", "sqlserver", "microsoft"}


class DatabaseCheck(BaseCheck):
    type = "database"

    def run(self, ctx: CheckContext) -> CheckResultData:
        cfg = ctx.config
        engine = str(cfg.get("engine", "postgresql")).lower()
        query = cfg.get("query", "SELECT 1")
        timeout = ctx.timeout_seconds
        host = ctx.hostname_or_ip

        t0 = time.time()
        try:
            if engine in PG_ALIASES:
                self._run_pg(host, cfg, query, timeout)
            elif engine in MYSQL_ALIASES:
                self._run_mysql(host, cfg, query, timeout)
            elif engine in ORACLE_ALIASES:
                self._run_oracle(host, cfg, query, timeout)
            elif engine in MSSQL_ALIASES:
                self._run_mssql(host, cfg, query, timeout)
            else:
                return CheckResultData(
                    status=CheckStatus.UNKNOWN, message=f"Moteur inconnu : {engine}"
                )
        except Exception as exc:  # noqa: BLE001
            return CheckResultData(
                status=CheckStatus.CRITICAL,
                message=f"Connexion {engine} échouée : {str(exc)[:120]}",
            )

        ms = int((time.time() - t0) * 1000)
        warn, crit = ctx.warning_threshold, ctx.critical_threshold
        if crit is not None and ms >= crit:
            status = CheckStatus.CRITICAL
        elif warn is not None and ms >= warn:
            status = CheckStatus.WARNING
        else:
            status = CheckStatus.OK
        return CheckResultData(
            status=status, value=float(ms),
            message=f"{engine} OK — requête en {ms} ms",
            perfdata={"response_ms": ms, "engine": engine},
        )

    def _run_pg(self, host, cfg, query, timeout):
        import psycopg2

        conn = psycopg2.connect(
            host=host, port=int(cfg.get("port", 5432)),
            user=cfg.get("user", "postgres"), password=cfg.get("password", ""),
            dbname=cfg.get("dbname", "postgres"), connect_timeout=timeout,
        )
        try:
            cur = conn.cursor()
            cur.execute(query)
            cur.fetchone()
        finally:
            conn.close()

    def _run_mysql(self, host, cfg, query, timeout):
        import pymysql

        conn = pymysql.connect(
            host=host, port=int(cfg.get("port", 3306)),
            user=cfg.get("user", "root"), password=cfg.get("password", ""),
            database=cfg.get("dbname") or None,
            connect_timeout=timeout, read_timeout=timeout,
        )
        try:
            cur = conn.cursor()
            cur.execute(query)
            cur.fetchone()
        finally:
            conn.close()

    def _run_oracle(self, host, cfg, query, timeout):
        import oracledb  # mode "thin" par défaut : aucun client Oracle requis

        service = cfg.get("dbname") or "XEPDB1"
        conn = oracledb.connect(
            user=cfg.get("user", "system"), password=cfg.get("password", ""),
            dsn=f"{host}:{int(cfg.get('port', 1521))}/{service}",
            tcp_connect_timeout=timeout,
        )
        try:
            cur = conn.cursor()
            cur.execute(query)
            cur.fetchone()
        finally:
            conn.close()

    def _run_mssql(self, host, cfg, query, timeout):
        import pymssql

        conn = pymssql.connect(
            server=host, port=str(int(cfg.get("port", 1433))),
            user=cfg.get("user", "sa"), password=cfg.get("password", ""),
            database=cfg.get("dbname") or "",
            login_timeout=timeout, timeout=timeout,
        )
        try:
            cur = conn.cursor()
            cur.execute(query)
            cur.fetchone()
        finally:
            conn.close()
