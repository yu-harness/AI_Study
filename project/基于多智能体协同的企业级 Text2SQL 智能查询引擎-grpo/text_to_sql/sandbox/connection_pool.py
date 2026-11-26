"""
Sandbox database connection pool.
"""

import json
import re
import time
import uuid
from contextlib import contextmanager
from typing import Optional

import redis
from sqlglot import exp, parse_one
from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import QueuePool


class SandboxConnectionPool:
    """Thin SQLAlchemy pool wrapper used by the sandbox executor."""

    def __init__(
        self,
        db_url: str,
        redis_url: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        query_timeout: int = 5,
    ):
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_pre_ping=True,
        )
        if self.engine.dialect.name == "sqlite":
            @event.listens_for(self.engine, "connect")
            def enable_sqlite_query_only(dbapi_connection, _):
                dbapi_connection.execute("PRAGMA query_only = ON")

        if redis_url.startswith("memory://"):
            raise ValueError("SandboxConnectionPool requires an external Redis service")
        self.redis = redis.from_url(redis_url)
        self.query_timeout = query_timeout

    @contextmanager
    def get_connection(self):
        """Yield a database connection and always close it."""

        conn = self.engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    def explain(self, sql: str, dialect: str = "mysql") -> dict:
        """Run EXPLAIN and extract rough cost information."""

        normalized_dialect = (dialect or "").lower().split("+", 1)[0]
        try:
            with self.get_connection() as conn:
                with self._enforce_query_timeout(conn, self.query_timeout):
                    if normalized_dialect == "oracle":
                        statement_id = uuid.uuid4().hex.upper()
                        conn.exec_driver_sql(
                            "EXPLAIN PLAN SET STATEMENT_ID = "
                            f"'{statement_id}' FOR {sql}"
                        )
                        result = conn.execute(
                            text(
                                'SELECT cardinality AS "ROW_COUNT", '
                                'cost AS "TOTAL_COST" '
                                "FROM plan_table "
                                "WHERE statement_id = :statement_id AND id = 0"
                            ),
                            {"statement_id": statement_id},
                        )
                        rows = result.fetchall()
                        conn.rollback()
                    else:
                        explain_sql = self._build_explain_sql(sql, normalized_dialect)
                        result = conn.execute(text(explain_sql))
                        rows = result.fetchall()
            return {
                "success": True,
                "estimated_rows": self._extract_rows(rows, normalized_dialect),
                "estimated_cost": self._extract_cost(rows, normalized_dialect),
                "plan": rows,
            }
        except Exception as exc:
            return {"success": False, "error": str(exc), "estimated_rows": 0}

    @staticmethod
    def _build_explain_sql(sql: str, dialect: str) -> str:
        """Build dialect-aware EXPLAIN SQL."""

        if re.match(r"^\s*EXPLAIN\b", sql or "", re.IGNORECASE):
            return sql

        dialect = (dialect or "").lower()
        if dialect == "mysql":
            return f"EXPLAIN FORMAT=JSON {sql}"
        if dialect == "postgresql":
            return f"EXPLAIN (FORMAT JSON) {sql}"
        if dialect == "oracle":
            return f"EXPLAIN PLAN FOR {sql}"
        if dialect.startswith("sqlite"):
            return f"EXPLAIN QUERY PLAN {sql}"
        return f"EXPLAIN {sql}"

    def execute(self, sql: str, limit: int = 1, timeout: int = None) -> dict:
        """Execute SQL with a final row limit."""

        dialect = self.engine.dialect.name.lower()
        timeout = self.query_timeout if timeout is None else timeout
        full_sql = self._append_limit(sql, limit, dialect)

        try:
            with self.get_connection() as conn:
                with self._enforce_query_timeout(conn, timeout):
                    result = conn.execute(text(full_sql))
                    rows = result.fetchall()
                    columns = result.keys()
                return {
                    "success": True,
                    "data": [dict(zip(columns, row)) for row in rows],
                    "row_count": len(rows),
                }
        except Exception as exc:
            return {"success": False, "error": str(exc), "data": []}

    @staticmethod
    def _append_limit(sql: str, limit: int, dialect: str) -> str:
        """Cap the statement's top-level result count with a dialect AST."""

        limit = int(limit)
        if limit <= 0:
            raise ValueError("SQL result limit must be a positive integer")
        base_sql = sql.rstrip()
        if base_sql.endswith(";"):
            base_sql = base_sql[:-1].rstrip()

        sqlglot_dialect = SandboxConnectionPool._sqlglot_dialect(dialect)
        statement = parse_one(base_sql, read=sqlglot_dialect)
        existing_limit = statement.args.get("limit")
        if existing_limit is not None:
            expression = existing_limit.args.get(
                "count" if isinstance(existing_limit, exp.Fetch) else "expression"
            )
            if not isinstance(expression, exp.Literal) or not expression.is_int:
                raise ValueError("SQL result limit must be an integer literal")
            if int(expression.this) <= limit:
                return statement.sql(dialect=sqlglot_dialect)

        statement.limit(limit, copy=False)
        return statement.sql(dialect=sqlglot_dialect)

    @staticmethod
    def _sqlglot_dialect(dialect: str) -> str:
        backend = (dialect or "").lower().split("+", 1)[0]
        return "postgres" if backend == "postgresql" else backend

    @contextmanager
    def _enforce_query_timeout(self, conn, timeout: int | float):
        seconds = float(timeout)
        if seconds <= 0:
            raise ValueError("Query timeout must be greater than zero")

        milliseconds = max(1, int(seconds * 1000))
        dialect = self.engine.dialect.name.lower()
        if dialect == "postgresql":
            conn.exec_driver_sql(f"SET LOCAL statement_timeout = {milliseconds}")
            yield
            return

        if dialect == "mysql":
            previous = int(
                conn.exec_driver_sql("SELECT @@SESSION.max_execution_time").scalar_one()
            )
            conn.exec_driver_sql(f"SET SESSION max_execution_time = {milliseconds}")
            try:
                yield
            finally:
                conn.exec_driver_sql(
                    f"SET SESSION max_execution_time = {previous}"
                )
            return

        dbapi_connection = conn.connection.driver_connection
        if dialect == "sqlite":
            deadline = time.monotonic() + seconds
            dbapi_connection.set_progress_handler(
                lambda: int(time.monotonic() >= deadline),
                1000,
            )
            try:
                yield
            finally:
                dbapi_connection.set_progress_handler(None, 0)
            return

        if dialect == "oracle":
            previous = dbapi_connection.call_timeout
            dbapi_connection.call_timeout = milliseconds
            try:
                yield
            finally:
                dbapi_connection.call_timeout = previous
            return

        raise ValueError(f"Query timeout is not implemented for dialect={dialect}")

    def _extract_rows(self, explain_rows, dialect: str) -> int:
        """Extract estimated rows from common EXPLAIN result shapes."""

        value = self._recursive_extract(explain_rows, ("rows", "Plan Rows", "ROW_COUNT", "row_count"))
        try:
            return int(value) if value is not None else 0
        except (TypeError, ValueError):
            return 0

    def _extract_cost(self, explain_rows, dialect: str) -> Optional[float]:
        """Extract estimated cost from common EXPLAIN result shapes."""

        value = self._recursive_extract(explain_rows, ("cost", "query_cost", "Cost", "TOTAL_COST", "total_cost"))
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def _recursive_extract(self, obj, keys):
        if isinstance(obj, bytes):
            obj = obj.decode("utf-8")
        if isinstance(obj, str):
            try:
                return self._recursive_extract(json.loads(obj), keys)
            except json.JSONDecodeError:
                return None
        if isinstance(obj, dict):
            for key in keys:
                if key in obj and obj[key] not in (None, "NULL"):
                    return obj[key]
            for value in obj.values():
                found = self._recursive_extract(value, keys)
                if found is not None:
                    return found
        if isinstance(obj, (list, tuple)):
            for item in obj:
                if hasattr(item, "_mapping"):
                    item = dict(item._mapping)
                elif hasattr(item, "keys"):
                    try:
                        item = dict(item)
                    except TypeError:
                        pass
                found = self._recursive_extract(item, keys)
                if found is not None:
                    return found
        return None

    def validate_connection(self) -> bool:
        """Return whether the sandbox database is reachable."""

        try:
            with self.get_connection() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.fetchone()[0] == 1
        except Exception:
            return False
