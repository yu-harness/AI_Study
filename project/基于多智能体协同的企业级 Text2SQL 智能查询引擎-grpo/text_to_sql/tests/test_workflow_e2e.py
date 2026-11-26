import unittest
from functools import partial

try:
    from text_to_sql.agents.coder_node import coder_node
    from text_to_sql.agents.executor_node import executor_node
    from text_to_sql.agents.state import build_initial_state
    from text_to_sql.agents.workflow import create_workflow, init_workflow
except ImportError as exc:  # pragma: no cover
    coder_node = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


class MockCoderAgent:
    def __init__(self, first_sql="SELECT id FROM users", repair_sql="SELECT id FROM users WHERE active = 1"):
        self.first_sql = first_sql
        self.repair_sql = repair_sql
        self.generate_calls = []
        self.repair_calls = 0

    def generate_with_retry(self, prompt, n=3):
        self.generate_calls.append(n)
        if isinstance(self.first_sql, list):
            return self.first_sql[:n]
        return [self.first_sql]

    def single_repair(self, prompt):
        self.repair_calls += 1
        if isinstance(self.repair_sql, list):
            idx = min(self.repair_calls - 1, len(self.repair_sql) - 1)
            return self.repair_sql[idx]
        return self.repair_sql


class MockExecutor:
    def __init__(self):
        self.pool = MockSandbox()

    def validate(self, sql, dialect="mysql"):
        if "bad_column" in sql:
            return False, "Unknown column bad_column", {"stage": "explain"}
        return True, "", {"stage": "validated", "estimated_rows": 1}

    def execute(self, sql, dialect="mysql"):
        return {"success": True, "data": [{"id": 1}], "row_count": 1}


class MockSandbox:
    def execute(self, sql, limit=10):
        return {"success": True, "data": [{"id": 1}], "row_count": 1}


class MockSelector:
    def select_best(self, sqls, query, sandbox, dialect="mysql"):
        return sqls[0] if sqls else ""


class MockCache:
    def __init__(self):
        self.values = {}

    def get(self, query):
        return self.values.get(query)

    def set(self, query, sql):
        self.values[query] = sql


@unittest.skipIf(IMPORT_ERROR is not None, f"workflow dependencies unavailable: {IMPORT_ERROR}")
class TestWorkflowE2E(unittest.TestCase):
    def setUp(self):
        self.cache = MockCache()
        self.executor = MockExecutor()
        self.selector = MockSelector()

    def _build_workflow(self, coder_agent, planner_fn=None, max_retries=3, max_candidates=3):
        def router(state):
            return {"target_db": "mock", "dialect": "mysql", "dialect_rules": []}

        def planner(state):
            return {
                "planner_output": {"execution_plan": "1. 确定主表：users"},
                "compressed_schema": "Table users:\n  - id (INT)\n  - active (INT)",
                "business_knowledge": "无",
                "value_mappings": [],
                "candidate_tables": ["users"],
            }

        init_workflow(
            router,
            planner_fn or planner,
            partial(coder_node, coder_agent=coder_agent, max_candidates=max_candidates),
            partial(executor_node, executor=self.executor, selector=self.selector, semantic_cache=self.cache),
        )
        return create_workflow(max_retries=max_retries)

    def test_success_path(self):
        workflow = self._build_workflow(MockCoderAgent(first_sql="SELECT id FROM users"))
        result = workflow.invoke(build_initial_state("查询用户"))
        self.assertEqual(result["final_sql"], "SELECT id FROM users")
        self.assertEqual(result["retry_count"], 0)
        self.assertEqual(result["error_history"], [])

    def test_retry_success_path(self):
        coder_agent = MockCoderAgent(
            first_sql="SELECT bad_column FROM users",
            repair_sql="SELECT id FROM users WHERE active = 1",
        )
        workflow = self._build_workflow(coder_agent)
        result = workflow.invoke(build_initial_state("查询活跃用户"))
        self.assertEqual(result["final_sql"], "SELECT id FROM users WHERE active = 1")
        self.assertEqual(result["retry_count"], 1)
        self.assertEqual(coder_agent.generate_calls, [3])
        self.assertEqual(coder_agent.repair_calls, 1)
        self.assertEqual(result["error_history"][0]["errors"][0]["stage"], "explain")
        trace_stages = [step["stage"] for step in result["debug_trace"]]
        self.assertIn("agent2", trace_stages)
        self.assertIn("sandbox", trace_stages)
        self.assertIn("reflection", trace_stages)

    def test_three_initial_candidates_fail_before_three_single_repairs(self):
        coder_agent = MockCoderAgent(
            first_sql=[
                "SELECT bad_column_1 FROM users",
                "SELECT bad_column_2 FROM users",
                "SELECT bad_column_3 FROM users",
            ],
            repair_sql=[
                "SELECT bad_column_4 FROM users",
                "SELECT bad_column_5 FROM users",
                "SELECT bad_column_6 FROM users",
            ],
        )

        workflow = self._build_workflow(coder_agent, max_retries=3, max_candidates=3)
        result = workflow.invoke(build_initial_state("鏌ヨ鐢ㄦ埛"))

        self.assertEqual(result["final_sql"], "")
        self.assertEqual(coder_agent.generate_calls, [3])
        self.assertEqual(coder_agent.repair_calls, 3)
        self.assertEqual(len(result["error_history"][0]["errors"]), 3)
        self.assertEqual(result["retry_count"], 4)

    def test_planner_cache_path_skips_coder_and_executor(self):
        def cached_planner(state):
            return {"final_sql": "SELECT id FROM cached_users", "cached": True}

        workflow = self._build_workflow(
            MockCoderAgent(first_sql="SELECT bad_column FROM users"),
            planner_fn=cached_planner,
        )
        result = workflow.invoke(build_initial_state("查询缓存用户"))
        self.assertEqual(result["final_sql"], "SELECT id FROM cached_users")
        self.assertTrue(result["cached"])
        self.assertEqual(result["retry_count"], 0)


if __name__ == "__main__":
    unittest.main()
