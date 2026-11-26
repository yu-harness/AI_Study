import unittest

from text_to_sql.sandbox.executor import SandboxExecutor
from text_to_sql.sandbox.executor import select_best_sql


class FakePool:
    def __init__(self):
        self.executed = []

    def execute(self, sql, limit=1):
        self.executed.append((sql, limit))
        return {"success": True, "data": [{"ok": 1}], "row_count": 1}


class TestSelectBestSQL(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(select_best_sql([]), "")

    def test_single_sql(self):
        self.assertEqual(select_best_sql(["SELECT * FROM users"]), "SELECT * FROM users")

    def test_prefer_where_clause(self):
        sqls = [
            "SELECT * FROM users",
            "SELECT * FROM users WHERE active = 1",
        ]
        self.assertEqual(select_best_sql(sqls), "SELECT * FROM users WHERE active = 1")

    def test_prefer_shorter_when_both_have_where(self):
        sqls = [
            "SELECT * FROM users WHERE active = 1 AND created_at > '2024-01-01'",
            "SELECT * FROM users WHERE active = 1",
        ]
        self.assertEqual(select_best_sql(sqls), "SELECT * FROM users WHERE active = 1")

    def test_prefer_non_select_star_when_other_scores_equal(self):
        sqls = [
            "SELECT * FROM users WHERE active = 1",
            "SELECT id FROM users WHERE active = 1",
        ]
        self.assertEqual(select_best_sql(sqls), "SELECT id FROM users WHERE active = 1")


class TestSandboxExecutor(unittest.TestCase):
    def test_execute_rechecks_security(self):
        pool = FakePool()
        executor = SandboxExecutor(pool)

        result = executor.execute("SELECT * FROM users; DROP TABLE users")

        self.assertFalse(result["success"])
        self.assertEqual(result["details"]["stage"], "security")
        self.assertEqual(pool.executed, [])

    def test_execute_delegates_safe_sql(self):
        pool = FakePool()
        executor = SandboxExecutor(pool)

        result = executor.execute("SELECT id FROM users", limit=5)

        self.assertTrue(result["success"])
        self.assertEqual(pool.executed, [("SELECT id FROM users", 5)])


if __name__ == "__main__":
    unittest.main()
