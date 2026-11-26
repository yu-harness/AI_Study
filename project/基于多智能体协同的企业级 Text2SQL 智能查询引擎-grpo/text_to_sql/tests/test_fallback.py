import unittest
from unittest.mock import MagicMock

from text_to_sql.agents.fallback import FallbackPlanner


class TestFallbackPlanner(unittest.TestCase):
    def setUp(self):
        self.mock_collector = MagicMock()
        self.mock_linker = MagicMock()
        self.planner = FallbackPlanner(self.mock_collector, self.mock_linker)

    def test_heuristic_parse_with_matched_tables(self):
        self.mock_linker.lookup_values.return_value = ["北京 -> city_id IN ('110000')"]
        self.mock_collector.get_all_table_names.return_value = ["user", "order", "product"]

        result = self.planner.heuristic_parse("查询 user 的订单")

        self.assertEqual(result["semantic_rewrite"], "查询 user 的订单")
        self.assertTrue(result["fallback"])
        self.assertIn("user", result["candidate_tables"])
        self.mock_collector.get_all_table_names.assert_called_once()

    def test_heuristic_parse_no_match_uses_hot_tables(self):
        self.mock_linker.lookup_values.return_value = []
        self.mock_collector.get_all_table_names.return_value = ["log", "config"]
        self.mock_collector.get_hot_tables.return_value = ["user", "order"]

        result = self.planner.heuristic_parse("随机查询")

        self.assertEqual(result["candidate_tables"], ["user", "order"])
        self.mock_collector.get_hot_tables.assert_called_once_with(top_k=5)


if __name__ == "__main__":
    unittest.main()
