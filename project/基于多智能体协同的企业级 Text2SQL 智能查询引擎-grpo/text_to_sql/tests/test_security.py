"""
Tests for sandbox/security.py
Corrected to match actual security logic.
"""
import unittest
from text_to_sql.sandbox.security import SQLSecurityChecker, security_check, get_security_checker


class TestSQLSecurityChecker(unittest.TestCase):
    def setUp(self):
        self.checker = SQLSecurityChecker()

    def test_safe_select(self):
        result = self.checker.check("SELECT * FROM users WHERE id = 1")
        self.assertTrue(result["safe"])

    def test_safe_with(self):
        result = self.checker.check("WITH tmp AS (SELECT * FROM users) SELECT * FROM tmp")
        self.assertTrue(result["safe"])

    def test_safe_explain(self):
        result = self.checker.check("EXPLAIN SELECT * FROM users")
        self.assertTrue(result["safe"])

    # DROP/DELETE/INSERT/UPDATE are blocked by whitelist first (not SELECT/WITH/EXPLAIN)
    # then blocked by blacklist if they somehow pass whitelist.
    def test_unsafe_drop_table_blocked_by_prefix(self):
        result = self.checker.check("DROP TABLE users")
        self.assertFalse(result["safe"])
        # Blocked at whitelist stage
        self.assertIn("SELECT/WITH/EXPLAIN", result["reason"])

    def test_delete_blocked_by_prefix(self):
        # DELETE is blocked because prefix is not SELECT/WITH/EXPLAIN
        result = self.checker.check("DELETE FROM users")
        self.assertFalse(result["safe"])
        self.assertIn("SELECT/WITH/EXPLAIN", result["reason"])

    def test_delete_with_where_blocked_by_prefix(self):
        result = self.checker.check("DELETE FROM users WHERE id = 1")
        self.assertFalse(result["safe"])
        self.assertIn("SELECT/WITH/EXPLAIN", result["reason"])

    def test_unsafe_insert_blocked_by_blacklist(self):
        # INSERT starts with INSERT, not in whitelist
        result = self.checker.check("INSERT INTO users (name) VALUES ('test')")
        self.assertFalse(result["safe"])

    def test_unsafe_update_blocked_by_blacklist(self):
        result = self.checker.check("UPDATE users SET name = 'test' WHERE id = 1")
        self.assertFalse(result["safe"])

    def test_unsafe_truncate_blocked_by_prefix(self):
        result = self.checker.check("TRUNCATE TABLE users")
        self.assertFalse(result["safe"])
        self.assertIn("SELECT/WITH/EXPLAIN", result["reason"])

    def test_unsafe_multiple_statements(self):
        result = self.checker.check("SELECT 1; DROP TABLE users")
        self.assertFalse(result["safe"])

    def test_dangerous_words_inside_string_literals_are_allowed(self):
        result = self.checker.check("SELECT 'DROP TABLE users -- not a comment' AS label")
        self.assertTrue(result["safe"])

    def test_comments_outside_string_literals_are_blocked(self):
        result = self.checker.check("SELECT 1 -- comment")
        self.assertFalse(result["safe"])

    def test_file_export_and_file_read_are_blocked(self):
        self.assertFalse(self.checker.check("SELECT * INTO OUTFILE '/tmp/users.csv' FROM users")["safe"])
        self.assertFalse(self.checker.check("SELECT LOAD_FILE('/etc/passwd')")["safe"])

    def test_quote_balance_valid(self):
        self.assertTrue(self.checker._check_quote_balance("SELECT * FROM users WHERE name = 'O''Reilly'"))

    def test_quote_balance_invalid(self):
        self.assertFalse(self.checker._check_quote_balance("SELECT * FROM users WHERE name = 'O'Reilly'"))

    def test_parentheses_balance(self):
        self.assertTrue(self.checker._check_quote_balance("SELECT * FROM (SELECT id FROM users) AS t"))
        self.assertFalse(self.checker._check_quote_balance("SELECT * FROM (SELECT id FROM users AS t"))

    def test_singleton(self):
        c1 = get_security_checker()
        c2 = get_security_checker()
        self.assertIs(c1, c2)

    def test_security_check_convenience(self):
        self.assertTrue(security_check("DROP TABLE users"))  # dangerous -> True
        self.assertFalse(security_check("SELECT 1"))          # safe -> False

    def test_union_select_legitimate(self):
        # 合法 UNION 查询不应被误拦截
        result = self.checker.check(
            "SELECT id FROM users WHERE active = 1 UNION SELECT id FROM admins WHERE active = 1"
        )
        self.assertTrue(result["safe"])


if __name__ == "__main__":
    unittest.main()
