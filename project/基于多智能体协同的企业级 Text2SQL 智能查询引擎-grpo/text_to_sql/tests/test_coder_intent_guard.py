import unittest

from text_to_sql.agents.coder_node import (
    filter_sqls_by_query_intent,
    validate_sql_matches_query_intent,
)


class TestCoderIntentGuard(unittest.TestCase):
    def test_detail_query_rejects_aggregation(self):
        reason = validate_sql_matches_query_intent(
            "SELECT SUM(amount), MIN(created_at) FROM orders WHERE status = 'paid'",
            "查询已支付订单的金额和创建时间",
        )

        self.assertIn("detail fields", reason)

    def test_unrequested_status_filter_is_rejected(self):
        reason = validate_sql_matches_query_intent(
            "SELECT user_id, SUM(amount) FROM orders WHERE status = 'paid' GROUP BY user_id",
            "统计每个用户的订单金额总和",
        )

        self.assertIn("status='paid'", reason)

    def test_unrequested_positive_amount_filter_is_rejected(self):
        reason = validate_sql_matches_query_intent(
            "SELECT user_id, SUM(amount) FROM orders WHERE amount >= 0 GROUP BY user_id",
            "统计每个用户的订单金额总和",
        )

        self.assertIn("amount >= 0", reason)

    def test_unrequested_active_filter_is_rejected(self):
        reason = validate_sql_matches_query_intent(
            "SELECT id, name FROM users WHERE active = 1",
            "查询所有用户的 id 和 name",
        )

        self.assertIn("active/enabled", reason)

    def test_unrequested_time_filter_is_rejected(self):
        reason = validate_sql_matches_query_intent(
            "SELECT amount FROM orders WHERE created_at >= '2026-01-01'",
            "查询订单金额",
        )

        self.assertIn("time range", reason)

    def test_explicit_paid_detail_filter_is_allowed(self):
        reason = validate_sql_matches_query_intent(
            "SELECT amount, created_at FROM orders WHERE status = 'paid'",
            "查询已支付订单的金额和创建时间",
        )

        self.assertEqual(reason, "")

    def test_explicit_aggregation_is_allowed(self):
        reason = validate_sql_matches_query_intent(
            "SELECT user_id, SUM(amount) FROM orders GROUP BY user_id",
            "统计每个用户的订单金额总和",
        )

        self.assertEqual(reason, "")

    def test_filter_reports_intent_errors_when_all_candidates_drift(self):
        accepted, errors = filter_sqls_by_query_intent(
            ["SELECT SUM(amount), MIN(created_at) FROM orders WHERE status = 'paid'"],
            "查询已支付订单的金额和创建时间",
        )

        self.assertEqual(accepted, [])
        self.assertEqual(errors[0]["stage"], "intent")


if __name__ == "__main__":
    unittest.main()
