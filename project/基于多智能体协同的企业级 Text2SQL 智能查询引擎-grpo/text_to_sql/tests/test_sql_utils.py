import unittest

from text_to_sql.agents.sql_utils import extract_readonly_sql, extract_sql, normalize_sql_candidates


class TestSQLUtils(unittest.TestCase):
    def test_extract_after_think(self):
        text = "<think>plan</think>\nSELECT * FROM users"
        self.assertEqual(extract_sql(text), "SELECT * FROM users")

    def test_extract_fenced_sql(self):
        text = "```sql\nSELECT id FROM users\n```"
        self.assertEqual(extract_sql(text), "SELECT id FROM users")

    def test_extract_from_prose(self):
        text = "最终 SQL：SELECT id FROM users WHERE active = 1"
        self.assertEqual(extract_sql(text), "SELECT id FROM users WHERE active = 1")

    def test_trim_after_first_statement(self):
        text = "SELECT 1; DROP TABLE users"
        self.assertEqual(extract_sql(text), "SELECT 1;")

    def test_reject_write_sql_for_readonly(self):
        self.assertEqual(extract_readonly_sql("DELETE FROM users"), "")

    def test_normalize_deduplicates(self):
        sqls = normalize_sql_candidates(["SELECT * FROM users", " select   * from users "])
        self.assertEqual(sqls, ["SELECT * FROM users"])


if __name__ == "__main__":
    unittest.main()
