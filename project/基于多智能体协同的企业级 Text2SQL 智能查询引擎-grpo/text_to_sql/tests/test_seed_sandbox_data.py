import sqlite3
import tempfile
from pathlib import Path
import unittest

from text_to_sql.runtime.seed_sandbox_data import seed_database


class TestSeedSandboxData(unittest.TestCase):
    def test_seed_database_creates_expected_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "sandbox.sqlite"

            counts = seed_database(
                "sqlite:///" + db_path.as_posix(),
                user_count=12,
                product_count=8,
                order_count=20,
                max_items_per_order=3,
                reset=True,
            )

            self.assertEqual(counts["users"], 12)
            self.assertEqual(counts["products"], 8)
            self.assertEqual(counts["orders"], 20)
            self.assertGreater(counts["order_items"], 20)
            self.assertGreater(counts["payments"], 0)

            conn = sqlite3.connect(db_path)
            try:
                table_counts = {
                    table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    for table in ("users", "products", "orders", "order_items", "payments")
                }
                foreign_key_count = sum(
                    len(conn.execute(f"PRAGMA foreign_key_list({table})").fetchall())
                    for table in ("orders", "order_items", "payments")
                )
            finally:
                conn.close()

            self.assertEqual(table_counts, counts)
            self.assertEqual(foreign_key_count, 4)


if __name__ == "__main__":
    unittest.main()
