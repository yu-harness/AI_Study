import unittest

from text_to_sql.training.data import result_signature
from text_to_sql.training.quality import (
    fingerprint_sql_ast,
    validate_dataset_quality,
    validate_evaluation_corpus,
    validate_grpo_split,
    validate_supervised_record_against_sandbox,
)


class FakeQualityExecutor:
    def __init__(self, rows, costs=None):
        self.rows = rows
        self.costs = costs or {}
        self.execute_calls = []

    def validate(self, sql, dialect):
        return True, "", {
            "stage": "validated",
            "estimated_rows": len(self.rows),
            "estimated_cost": self.costs.get(sql),
        }

    def execute(self, sql, dialect, limit):
        self.execute_calls.append((sql, dialect, limit))
        return {"success": True, "data": self.rows[:limit]}


def _quality_record(record_id, difficulty, embedding):
    return {
        "id": record_id,
        "instruction": "查询订单编号",
        "input": "【压缩Schema】orders(id)",
        "output": "SELECT id FROM orders",
        "dialect": "sqlite",
        "difficulty": difficulty,
        "schema_verified": True,
        "business_definition_verified": True,
        "query_semantic_fingerprint": f"query-{record_id}",
        "sql_ast_fingerprint": fingerprint_sql_ast("SELECT id FROM orders", "sqlite"),
        "gold_result_signature": result_signature([{"id": 1}]),
        "query_embedding": embedding,
    }


def _evaluation_corpus():
    records = []
    offset = 0
    for difficulty, count in (("easy", 750), ("medium", 1_250), ("hard", 500)):
        records.extend(
            {
                "id": f"eval-{offset + index}",
                "difficulty": difficulty,
                "query_embedding": [1.0, 0.0],
            }
            for index in range(count)
        )
        offset += count
    return records


class TestTrainingQuality(unittest.TestCase):
    def test_dataset_quality_enforces_count_distribution_and_eval_leakage(self):
        records = [
            _quality_record("1", "easy", [1.0, 0.0]),
            _quality_record("2", "hard", [0.0, 1.0]),
        ]
        evaluation = [{"id": "eval-1", "query_embedding": [1.0, 0.0]}]

        issues = validate_dataset_quality(
            records,
            "sft",
            expected_total=3,
            difficulty_targets={"easy": 0.25, "medium": 0.50, "hard": 0.25},
            difficulty_tolerance=0.01,
            sensitive_fields=["password"],
            evaluation_records=evaluation,
        )

        self.assertTrue(any(issue.field == "$dataset" for issue in issues))
        self.assertTrue(any(issue.field == "difficulty" for issue in issues))
        self.assertTrue(any("evaluation leakage" in issue.message for issue in issues))

    def test_dataset_quality_rejects_sensitive_columns_and_duplicate_fingerprints(self):
        first = _quality_record("1", "easy", [1.0, 0.0])
        first["output"] = "SELECT password FROM users"
        second = dict(first, id="2", query_embedding=[0.0, 1.0])

        issues = validate_dataset_quality(
            [first, second],
            "sft",
            sensitive_fields=["users.password", "password"],
        )

        self.assertEqual(sum("sensitive fields" in issue.message for issue in issues), 2)
        self.assertTrue(any("duplicate training sample" in issue.message for issue in issues))

    def test_sensitive_gate_resolves_table_aliases(self):
        record = _quality_record("alias", "easy", [1.0, 0.0])
        record["output"] = "SELECT u.password FROM users AS u"
        record["sql_ast_fingerprint"] = fingerprint_sql_ast(record["output"], "sqlite")

        issues = validate_dataset_quality(
            [record],
            "sft",
            sensitive_fields=["users.password"],
        )

        self.assertTrue(any("users.password" in issue.message for issue in issues))

    def test_embedding_gate_reports_zero_vector_without_skipping_other_rows(self):
        records = [
            _quality_record("zero", "easy", [0.0, 0.0]),
            _quality_record("leaked", "medium", [1.0, 0.0]),
        ]

        issues = validate_dataset_quality(
            records,
            "sft",
            sensitive_fields=["password"],
            evaluation_records=[{"id": "eval-1", "query_embedding": [1.0, 0.0]}],
        )

        self.assertTrue(any(issue.sample_id == "zero" and "zero vector" in issue.message for issue in issues))
        self.assertTrue(
            any(issue.sample_id == "leaked" and "evaluation leakage" in issue.message for issue in issues)
        )

    def test_embedding_gate_rejects_non_finite_values(self):
        issues = validate_dataset_quality(
            [_quality_record("nan", "easy", [float("nan"), 0.0])],
            "sft",
            sensitive_fields=["password"],
            evaluation_records=[{"id": "eval-1", "query_embedding": [1.0, 0.0]}],
        )

        self.assertTrue(any(issue.sample_id == "nan" and "finite" in issue.message for issue in issues))

    def test_evaluation_corpus_gate_locks_count_distribution_and_ids(self):
        self.assertEqual(validate_evaluation_corpus(_evaluation_corpus()), [])

        invalid = _evaluation_corpus()[:-1]
        invalid[1]["id"] = invalid[0]["id"]
        issues = validate_evaluation_corpus(invalid)

        self.assertTrue(any("exactly 2500" in issue.message for issue in issues))
        self.assertTrue(any("hard count must be 500" in issue.message for issue in issues))
        self.assertTrue(any("duplicate evaluation id" in issue.message for issue in issues))

    def test_sft_think_gate_accepts_documented_mode_distribution(self):
        records = []
        for index in range(10):
            record = _quality_record(f"easy-{index}", "easy", [1.0, float(index + 1)])
            if index >= 7:
                record["output"] = "<think>读取订单编号。</think>\nSELECT id FROM orders"
            records.append(record)
        for difficulty in ("medium", "hard"):
            record = _quality_record(difficulty, difficulty, [2.0, 1.0])
            record["output"] = (
                "<think>\n1. 使用 orders 表。\n2. 读取 id 字段。\n</think>\n"
                "SELECT id FROM orders"
            )
            record["reasoning_verified"] = True
            records.append(record)

        issues = validate_dataset_quality(records, "sft")

        self.assertEqual(issues, [])

    def test_sft_think_gate_rejects_wrong_easy_ratio_and_missing_reasoning(self):
        records = [
            _quality_record(f"easy-{index}", "easy", [1.0, float(index + 1)])
            for index in range(10)
        ]
        records.append(_quality_record("medium", "medium", [2.0, 1.0]))
        hard = _quality_record("hard", "hard", [3.0, 1.0])
        hard["output"] = "<think>  </think>\nSELECT id FROM orders"
        records.append(hard)

        issues = validate_dataset_quality(records, "sft")

        self.assertTrue(any("easy samples without <think>" in issue.message for issue in issues))
        self.assertTrue(
            any(issue.sample_id == "medium" and "require a non-empty" in issue.message for issue in issues)
        )
        self.assertTrue(
            any(issue.sample_id == "hard" and "non-empty leading block" in issue.message for issue in issues)
        )

    def test_sft_think_gate_rejects_unstructured_or_unverified_reasoning(self):
        unstructured = _quality_record("medium", "medium", [1.0, 0.0])
        unstructured["output"] = "<think>x</think>\nSELECT id FROM orders"
        unstructured["reasoning_verified"] = True
        unverified = _quality_record("hard", "hard", [0.0, 1.0])
        unverified["output"] = (
            "<think>\n1. 使用 orders 表。\n2. 读取 id 字段。\n</think>\n"
            "SELECT id FROM orders"
        )

        issues = validate_dataset_quality([unstructured, unverified], "sft")

        self.assertTrue(
            any(
                issue.sample_id == "medium" and "at least two structured" in issue.message
                for issue in issues
            )
        )
        self.assertTrue(
            any(
                issue.sample_id == "hard" and issue.field == "reasoning_verified"
                for issue in issues
            )
        )

    def test_sft_sandbox_gate_executes_complete_result_and_checks_signature(self):
        rows = [{"id": 1}, {"id": 2}]
        executor = FakeQualityExecutor(rows)
        record = {
            "id": "sft-1",
            "instruction": "查询订单编号",
            "input": "schema",
            "output": "SELECT id FROM orders ORDER BY id",
            "target_db": "local_sqlite",
            "dialect": "sqlite",
            "gold_result_signature": result_signature(rows),
            "reward_meta": {
                "preserve_result_order": True,
                "result_limit": 2,
                "max_estimated_rows": 100,
            },
        }

        issues = validate_supervised_record_against_sandbox(
            record,
            "sft",
            sandbox_db_urls={"local_sqlite": "sqlite:///sandbox.sqlite"},
            redis_url="redis://127.0.0.1:6379/0",
            sensitive_fields=["password"],
            executor_factory=lambda **_: executor,
        )

        self.assertEqual(issues, [])
        self.assertEqual(executor.execute_calls[0][2], 3)

    def test_sft_sandbox_gate_rejects_result_order_metadata_mismatch(self):
        executor = FakeQualityExecutor([{"id": 1}, {"id": 2}])
        record = {
            "id": "sft-order",
            "instruction": "按编号查询订单",
            "input": "schema",
            "output": "SELECT id FROM orders ORDER BY id",
            "target_db": "local_sqlite",
            "dialect": "sqlite",
            "gold_result_signature": result_signature(
                [{"id": 1}, {"id": 2}],
                preserve_order=False,
            ),
            "reward_meta": {
                "preserve_result_order": False,
                "result_limit": 2,
                "max_estimated_rows": 100,
            },
        }

        issues = validate_supervised_record_against_sandbox(
            record,
            "sft",
            sandbox_db_urls={"local_sqlite": "sqlite:///sandbox.sqlite"},
            redis_url="redis://127.0.0.1:6379/0",
            sensitive_fields=[],
            executor_factory=lambda **_: executor,
        )

        self.assertTrue(any(issue.field == "reward_meta.preserve_result_order" for issue in issues))
        self.assertEqual(executor.execute_calls, [])

    def test_dpo_sandbox_gate_requires_both_correct_and_chosen_not_costlier(self):
        rows = [{"id": 1}]
        chosen = "SELECT id FROM orders"
        rejected = "SELECT id FROM orders WHERE id > 0"
        executor = FakeQualityExecutor(rows, costs={chosen: 20, rejected: 10})
        record = {
            "id": "dpo-1",
            "instruction": "查询订单编号",
            "input": "schema",
            "chosen": chosen,
            "rejected": rejected,
            "preference_verified": True,
            "preference_reason": "chosen should have a cheaper plan",
            "target_db": "local_sqlite",
            "dialect": "sqlite",
            "gold_result_signature": result_signature(rows, preserve_order=False),
            "reward_meta": {
                "preserve_result_order": False,
                "result_limit": 10,
                "max_estimated_rows": 100,
            },
        }

        issues = validate_supervised_record_against_sandbox(
            record,
            "dpo",
            sandbox_db_urls={"local_sqlite": "sqlite:///sandbox.sqlite"},
            redis_url="redis://127.0.0.1:6379/0",
            sensitive_fields=[],
            executor_factory=lambda **_: executor,
        )

        self.assertTrue(any("chosen estimated cost" in issue.message for issue in issues))

    def test_grpo_split_gate_rejects_wrong_sizes_and_template_leakage(self):
        train = [
            {
                "id": "1",
                "difficulty": "hard",
                "business_template_id": "shared",
                "query_semantic_fingerprint": "query-1",
                "sql_ast_fingerprint": "ast-1",
                "schema_fingerprint": "schema-1",
            }
        ]
        valid = [
            {
                "id": "2",
                "difficulty": "medium",
                "business_template_id": "shared",
                "query_semantic_fingerprint": "query-2",
                "sql_ast_fingerprint": "ast-2",
                "schema_fingerprint": "schema-2",
            }
        ]

        issues = validate_grpo_split(train, valid, [])

        self.assertTrue(any(issue.field == "split" for issue in issues))
        self.assertTrue(any("crosses" in issue.message for issue in issues))

    def test_grpo_split_gate_requires_unique_fingerprints_across_all_splits(self):
        fingerprint = {
            "query_semantic_fingerprint": "query-1",
            "sql_ast_fingerprint": "ast-1",
            "schema_fingerprint": "schema-1",
        }
        train = [
            {
                "id": "1",
                "difficulty": "hard",
                "business_template_id": "train-template",
                **fingerprint,
            }
        ]
        valid = [
            {
                "id": "2",
                "difficulty": "medium",
                "business_template_id": "valid-template",
                **fingerprint,
            }
        ]
        holdout = [
            {
                "id": "3",
                "difficulty": "medium",
                "business_template_id": "holdout-template",
            }
        ]

        issues = validate_grpo_split(train, valid, holdout)

        self.assertTrue(any("duplicate GRPO sample fingerprint" in issue.message for issue in issues))
        self.assertTrue(
            any(issue.sample_id == "3" and issue.field == "fingerprints" for issue in issues)
        )


if __name__ == "__main__":
    unittest.main()
