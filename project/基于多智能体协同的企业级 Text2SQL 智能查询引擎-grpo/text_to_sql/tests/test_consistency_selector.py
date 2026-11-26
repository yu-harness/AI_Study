import unittest

from text_to_sql.agents.consistency_selector import ConsistencySelector


class FakeExecutor:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def execute(self, sql, dialect="mysql", limit=1):
        self.calls.append({"sql": sql, "dialect": dialect, "limit": limit})
        return {"success": True, "data": self.results[sql], "row_count": len(self.results[sql])}


class FakeJudge:
    def __init__(self, response):
        self.response = response
        self.prompts = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return self.response


class TestConsistencySelector(unittest.TestCase):
    def test_unique_majority_prefers_best_sql_inside_majority(self):
        results = {
            "SELECT * FROM users WHERE id = 1": [{"id": 1, "name": "Ada"}],
            "SELECT id, name FROM users WHERE id = 1": [{"id": 1, "name": "Ada"}],
            "SELECT id, name FROM users WHERE id = 2": [{"id": 2, "name": "Lin"}],
        }
        selector = ConsistencySelector()

        selected = selector.select_best(list(results), "find user", FakeExecutor(results), dialect="sqlite")

        self.assertEqual(selected, "SELECT id, name FROM users WHERE id = 1")

    def test_no_majority_uses_judge_instead_of_first_candidate(self):
        results = {
            "SELECT id FROM users WHERE id = 1": [{"id": 1}],
            "SELECT id FROM users WHERE id = 2": [{"id": 2}],
            "SELECT id FROM users WHERE id = 3": [{"id": 3}],
        }
        judge = FakeJudge("2")
        selector = ConsistencySelector(judge_llm=judge)

        selected = selector.select_best(list(results), "find best user", FakeExecutor(results), dialect="sqlite")

        self.assertEqual(selected, "SELECT id FROM users WHERE id = 2")
        self.assertEqual(len(judge.prompts), 1)

    def test_selector_passes_dialect_and_limit_to_executor(self):
        results = {"SELECT id FROM users": [{"id": 1}]}
        executor = FakeExecutor(results)
        selector = ConsistencySelector()

        selector.select_best(["SELECT id FROM users"], "list users", executor, dialect="sqlite")

        self.assertEqual(executor.calls, [])

    def test_selector_passes_dialect_and_limit_for_multiple_candidates(self):
        results = {
            "SELECT id FROM users WHERE id = 1": [{"id": 1}],
            "SELECT id FROM users WHERE id = 2": [{"id": 2}],
        }
        executor = FakeExecutor(results)
        selector = ConsistencySelector()

        selector.select_best(list(results), "list users", executor, dialect="sqlite")

        self.assertEqual(executor.calls[0], {"sql": "SELECT id FROM users WHERE id = 1", "dialect": "sqlite", "limit": 10})


if __name__ == "__main__":
    unittest.main()
