import sqlite3
import unittest
from contextlib import nullcontext
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from text_to_sql.sandbox.connection_pool import SandboxConnectionPool


class TestLimitInjection(unittest.TestCase):
    def test_adds_limit_when_missing(self):
        sql = "SELECT * FROM users"
        result = SandboxConnectionPool._append_limit(sql, 5, "mysql")
        self.assertEqual(result, "SELECT * FROM users LIMIT 5")

    def test_caps_limit_when_already_present(self):
        sql = "SELECT * FROM users LIMIT 10"
        result = SandboxConnectionPool._append_limit(sql, 5, "mysql")
        self.assertEqual(result, "SELECT * FROM users LIMIT 5")

    def test_caps_limit_with_offset(self):
        sql = "SELECT * FROM users LIMIT 10 OFFSET 20"
        result = SandboxConnectionPool._append_limit(sql, 5, "sqlite")
        self.assertEqual(result, "SELECT * FROM users LIMIT 5 OFFSET 20")

    def test_caps_mysql_comma_limit(self):
        sql = "SELECT * FROM users LIMIT 20, 10"
        result = SandboxConnectionPool._append_limit(sql, 5, "mysql")
        self.assertEqual(result, "SELECT * FROM users LIMIT 5 OFFSET 20")

    def test_caps_fetch_first_limit(self):
        sql = "SELECT * FROM users FETCH FIRST 10 ROWS ONLY"
        result = SandboxConnectionPool._append_limit(sql, 5, "postgresql")
        self.assertEqual(result, "SELECT * FROM users LIMIT 5")

    def test_caps_limit_with_trailing_whitespace(self):
        sql = "SELECT * FROM users LIMIT 10   "
        result = SandboxConnectionPool._append_limit(sql, 5, "mysql")
        self.assertEqual(result, "SELECT * FROM users LIMIT 5")

    def test_caps_oracle_fetch_with_rownum(self):
        sql = "SELECT * FROM users FETCH FIRST 10 ROWS ONLY"
        result = SandboxConnectionPool._append_limit(sql, 5, "oracle")
        self.assertEqual(result, "SELECT * FROM users FETCH FIRST 5 ROWS ONLY")

    def test_preserves_smaller_existing_limit(self):
        result = SandboxConnectionPool._append_limit(
            "SELECT id FROM users LIMIT 3",
            5,
            "mysql",
        )

        self.assertEqual(result, "SELECT id FROM users LIMIT 3")

    def test_caps_limit_before_for_update_without_duplicate_limit(self):
        result = SandboxConnectionPool._append_limit(
            "SELECT id FROM users LIMIT 100 FOR UPDATE",
            5,
            "mysql",
        )

        self.assertEqual(result, "SELECT id FROM users LIMIT 5 FOR UPDATE")

    def test_adds_limit_to_subquery_like(self):
        sql = "SELECT * FROM (SELECT * FROM t LIMIT 5) AS sub"
        result = SandboxConnectionPool._append_limit(sql, 3, "mysql")
        self.assertEqual(result, "SELECT * FROM (SELECT * FROM t LIMIT 5) AS sub LIMIT 3")

    def test_strips_trailing_semicolon_before_limit(self):
        sql = "SELECT * FROM users;"
        result = SandboxConnectionPool._append_limit(sql, 5, "mysql")
        self.assertEqual(result, "SELECT * FROM users LIMIT 5")

    def test_explain_sql_is_not_explained_twice(self):
        sql = "EXPLAIN SELECT * FROM users"
        result = SandboxConnectionPool._build_explain_sql(sql, "mysql")
        self.assertEqual(result, sql)

    def test_oracle_explain_reads_plan_table_before_rollback(self):
        pool = object.__new__(SandboxConnectionPool)
        pool.query_timeout = 5
        connection = MagicMock()
        connection.execute.return_value.fetchall.return_value = [
            {"ROW_COUNT": 123, "TOTAL_COST": 45.5}
        ]
        pool.get_connection = MagicMock(return_value=nullcontext(connection))
        pool._enforce_query_timeout = MagicMock(return_value=nullcontext())

        result = pool.explain("SELECT * FROM orders", dialect="oracle")

        self.assertTrue(result["success"])
        self.assertEqual(result["estimated_rows"], 123)
        self.assertEqual(result["estimated_cost"], 45.5)
        explain_sql = connection.exec_driver_sql.call_args.args[0]
        self.assertRegex(
            explain_sql,
            r"^EXPLAIN PLAN SET STATEMENT_ID = '[0-9A-F]{32}' FOR SELECT \* FROM orders$",
        )
        plan_parameters = connection.execute.call_args.args[1]
        self.assertIn(plan_parameters["statement_id"], explain_sql)
        connection.rollback.assert_called_once_with()


class TestSQLiteReadOnlyPool(unittest.TestCase):
    def test_sqlite_target_allows_select_and_rejects_write(self):
        with TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp_dir:
            db_path = Path(temp_dir) / "sandbox.sqlite"
            connection = sqlite3.connect(db_path)
            connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
            connection.execute("INSERT INTO users (name) VALUES ('Ada')")
            connection.execute("INSERT INTO users (name) VALUES ('Linus')")
            connection.commit()
            connection.close()

            pool = SandboxConnectionPool(
                f"sqlite:///{db_path.as_posix()}",
                "redis://127.0.0.1:6379/15",
            )
            try:
                with patch.object(
                    pool,
                    "_enforce_query_timeout",
                    wraps=pool._enforce_query_timeout,
                ) as enforce_timeout:
                    explained = pool.explain("SELECT name FROM users", dialect="sqlite")
                selected = pool.execute("SELECT name FROM users", limit=5)
                capped = pool.execute("SELECT name FROM users LIMIT 1000000", limit=1)
                with self.assertRaises(OperationalError) as raised:
                    with pool.get_connection() as pooled_connection:
                        pooled_connection.execute(text("INSERT INTO users (name) VALUES ('Grace')"))
            finally:
                pool.engine.dispose()

        self.assertTrue(selected["success"])
        self.assertTrue(explained["success"])
        enforce_timeout.assert_called_once()
        self.assertEqual(selected["data"], [{"name": "Ada"}, {"name": "Linus"}])
        self.assertEqual(capped["row_count"], 1)
        self.assertIn("readonly", str(raised.exception).lower())

    def test_sqlite_query_timeout_interrupts_long_running_select(self):
        with TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp_dir:
            db_path = Path(temp_dir) / "sandbox.sqlite"
            sqlite3.connect(db_path).close()
            pool = SandboxConnectionPool(
                f"sqlite:///{db_path.as_posix()}",
                "redis://127.0.0.1:6379/15",
                query_timeout=0.001,
            )
            try:
                result = pool.execute(
                    """
                    WITH RECURSIVE counter(value) AS (
                        SELECT 1
                        UNION ALL
                        SELECT value + 1 FROM counter WHERE value < 100000000
                    )
                    SELECT SUM(value) AS total FROM counter
                    """,
                    limit=1,
                )
            finally:
                pool.engine.dispose()

        self.assertFalse(result["success"])
        self.assertIn("interrupted", result["error"].lower())


if __name__ == "__main__":
    unittest.main()
