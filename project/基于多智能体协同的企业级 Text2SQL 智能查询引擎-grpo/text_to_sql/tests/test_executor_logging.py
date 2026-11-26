import unittest
from unittest.mock import Mock, patch

from text_to_sql.agents.executor_node import executor_node


class TestExecutorStructuredLogging(unittest.TestCase):
    def test_validation_failure_logs_required_context(self):
        executor = Mock()
        executor.validate.return_value = (False, "forbidden statement", {"stage": "security"})
        state = {
            "query": "查询用户",
            "candidate_sqls": ["DROP TABLE users"],
            "dialect": "sqlite",
            "retry_count": 2,
            "fallback": True,
            "error_history": [],
            "debug_trace": [],
        }

        with patch("text_to_sql.agents.executor_node.logger") as logger:
            executor_node(state, executor, Mock(), Mock())

        fields = logger.warning.call_args_list[0].kwargs
        self.assertEqual(fields["sql"], "DROP TABLE users")
        self.assertEqual(fields["error_msg"], "forbidden statement")
        self.assertEqual(fields["retry_count"], 2)
        self.assertTrue(fields["fallback"])


if __name__ == "__main__":
    unittest.main()
