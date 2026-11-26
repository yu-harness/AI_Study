import tempfile
import unittest
from pathlib import Path

from text_to_sql.training.data import (
    _sql_leaks,
    assemble_grpo_prompt,
    result_signature,
    split_records,
    strict_readonly_sql,
    validate_dpo_record,
    validate_grpo_gold_record,
    validate_grpo_record,
    validate_jsonl,
    validate_sft_record,
    write_grpo_parquet,
    write_jsonl,
)


class FakeGoldExecutor:
    def __init__(self, rows, estimated_rows=0):
        self.rows = rows
        self.estimated_rows = estimated_rows
        self.execute_calls = []

    def validate(self, sql, dialect):
        return True, "", {
            "stage": "validated",
            "estimated_rows": self.estimated_rows,
        }

    def execute(self, sql, dialect, limit):
        self.execute_calls.append((sql, dialect, limit))
        return {"success": True, "data": self.rows}


class TestTrainingData(unittest.TestCase):
    def test_valid_sft_record_accepts_doc_format(self):
        record = {
            "instruction": "查询上个月华东区销售额排名前三的商品",
            "input": "【压缩Schema】\nTable orders:\n  - amount (decimal)",
            "output": "<think>先按商品聚合销售额，再倒序取前三。</think>\nSELECT product_id, SUM(amount) AS total_amount FROM orders GROUP BY product_id ORDER BY total_amount DESC LIMIT 3;",
            "history": [],
        }

        self.assertEqual(validate_sft_record(record), [])

    def test_sft_record_rejects_write_sql(self):
        record = {
            "instruction": "删除订单",
            "input": "【压缩Schema】orders",
            "output": "DELETE FROM orders",
        }

        issues = validate_sft_record(record)
        self.assertTrue(any(issue.field == "output" for issue in issues))

    def test_sft_record_rejects_prose_after_sql(self):
        record = {
            "instruction": "查询订单",
            "input": "【压缩Schema】orders",
            "output": "SELECT * FROM orders\n这里是解释",
        }

        issues = validate_sft_record(record)
        self.assertTrue(any(issue.field == "output" for issue in issues))

    def test_sft_record_rejects_write_cte(self):
        record = {
            "instruction": "删除后返回订单",
            "input": "【压缩Schema】orders",
            "output": "WITH deleted AS (DELETE FROM orders RETURNING *) SELECT * FROM deleted",
        }

        issues = validate_sft_record(record)

        self.assertTrue(any(issue.field == "output" for issue in issues))

    def test_sft_record_rejects_non_deterministic_sql(self):
        record = {
            "instruction": "生成随机数",
            "input": "【压缩Schema】dual",
            "output": "SELECT RAND() AS value",
        }

        issues = validate_sft_record(record)

        self.assertTrue(any("non-deterministic" in issue.message for issue in issues))

    def test_dpo_record_rejects_write_cte(self):
        record = {
            "instruction": "查询订单",
            "input": "【压缩Schema】orders",
            "chosen": "SELECT * FROM orders",
            "rejected": "WITH deleted AS (DELETE FROM orders RETURNING *) SELECT * FROM deleted",
        }

        issues = validate_dpo_record(record)

        self.assertTrue(any(issue.field == "rejected" for issue in issues))

    def test_grpo_prompt_excludes_gold_sql_and_validates_markers(self):
        prompt = assemble_grpo_prompt(
            query="查询订单数",
            compressed_schema="Table orders:\n  - id (int)",
            business_knowledge="订单数=count(id)",
            value_mappings=[],
            dialect_rules=["Use SQLite syntax."],
        )
        gold_sql = "SELECT COUNT(*) FROM orders;"
        record = {
            "id": "rl_001",
            "difficulty": "medium",
            "target_db": "local_sqlite",
            "dialect": "sqlite",
            "query": "查询订单数",
            "prompt": prompt,
            "gold_sql": gold_sql,
            "gold_result_signature": result_signature([{"count": 3}]),
            "reward_meta": {
                "required_tables": ["orders"],
                "non_empty_result": True,
                "preserve_result_order": False,
                "result_limit": 1000,
                "max_estimated_rows": 10000000,
            },
        }

        self.assertNotIn(gold_sql, prompt)
        self.assertEqual(validate_grpo_record(record), [])

    def test_grpo_record_requires_target_database_route(self):
        record = {
            "id": "rl_001",
            "difficulty": "hard",
            "dialect": "sqlite",
            "query": "查询订单数",
            "prompt": assemble_grpo_prompt("查询订单数", "schema"),
            "gold_sql": "SELECT COUNT(*) FROM orders",
            "gold_result_signature": result_signature([{"count": 3}]),
            "reward_meta": {},
        }

        issues = validate_grpo_record(record)

        self.assertTrue(any(issue.field == "target_db" for issue in issues))

    def test_grpo_record_rejects_gold_sql_leakage(self):
        gold_sql = "SELECT COUNT(*) FROM orders;"
        record = {
            "id": "rl_001",
            "difficulty": "hard",
            "target_db": "local_sqlite",
            "dialect": "sqlite",
            "query": "查询订单数",
            "prompt": assemble_grpo_prompt("查询订单数", "schema") + "\n" + gold_sql,
            "gold_sql": gold_sql,
            "gold_result_signature": result_signature([{"count": 3}]),
            "reward_meta": {},
        }

        issues = validate_grpo_record(record)
        self.assertTrue(any("gold_sql" in issue.message for issue in issues))

    def test_grpo_record_rejects_normalized_gold_sql_leakage(self):
        gold_sql = "SELECT COUNT(*) FROM orders;"
        record = {
            "id": "rl_001",
            "difficulty": "hard",
            "target_db": "local_sqlite",
            "dialect": "sqlite",
            "query": "查询订单数",
            "prompt": assemble_grpo_prompt("查询订单数", "schema") + "\nselect count(*) from orders",
            "gold_sql": gold_sql,
            "gold_result_signature": result_signature([{"count": 3}]),
            "reward_meta": {},
        }

        issues = validate_grpo_record(record)
        self.assertTrue(any("gold_sql" in issue.message for issue in issues))

    def test_grpo_record_rejects_quoted_or_commented_gold_sql_leakage(self):
        gold_sql = "SELECT id FROM orders"
        for leaked_sql in (
            "SELECT [id] FROM [orders]",
            "SELECT /* hidden label */ `id` FROM `orders`",
            'SELECT "id" FROM "orders"',
        ):
            with self.subTest(leaked_sql=leaked_sql):
                record = {
                    "id": "rl_001",
                    "difficulty": "hard",
                    "target_db": "local_sqlite",
                    "dialect": "sqlite",
                    "query": "查询订单编号",
                    "prompt": assemble_grpo_prompt("查询订单编号", "schema") + "\n" + leaked_sql,
                    "gold_sql": gold_sql,
                    "gold_result_signature": result_signature([{"id": 1}]),
                    "reward_meta": {
                        "required_tables": ["orders"],
                        "non_empty_result": True,
                        "preserve_result_order": False,
                        "result_limit": 1000,
                        "max_estimated_rows": 10_000_000,
                    },
                }

                issues = validate_grpo_record(record)

                self.assertTrue(any("gold_sql" in issue.message for issue in issues))

    def test_grpo_record_rejects_semantically_equivalent_gold_sql_leakage(self):
        gold_sql = (
            "SELECT id FROM orders "
            "WHERE status = 'paid' AND region = 'east'"
        )
        for leaked_sql in (
            "SELECT orders.id FROM orders "
            "WHERE status = 'paid' AND region = 'east'",
            "SELECT id FROM orders "
            "WHERE 'east' = region AND 'paid' = status",
            "SELECT o.id\nFROM orders AS o\n"
            "WHERE o.region = 'east' AND o.status = 'paid'",
        ):
            with self.subTest(leaked_sql=leaked_sql):
                record = {
                    "id": "rl_001",
                    "difficulty": "hard",
                    "target_db": "local_sqlite",
                    "dialect": "sqlite",
                    "query": "查询华东区已支付订单",
                    "prompt": (
                        assemble_grpo_prompt("查询华东区已支付订单", "orders(id,status,region)")
                        + "\n"
                        + leaked_sql
                    ),
                    "gold_sql": gold_sql,
                    "gold_result_signature": result_signature([{"id": 1}]),
                    "reward_meta": {
                        "required_tables": ["orders"],
                        "non_empty_result": True,
                        "preserve_result_order": False,
                        "result_limit": 1000,
                        "max_estimated_rows": 10_000_000,
                    },
                }

                issues = validate_grpo_record(record)

                self.assertTrue(any("gold_sql" in issue.message for issue in issues))

    def test_grpo_record_allows_a_different_sql_example_in_prompt(self):
        record = {
            "id": "rl_001",
            "difficulty": "hard",
            "target_db": "local_sqlite",
            "dialect": "sqlite",
            "query": "查询已支付订单",
            "prompt": (
                assemble_grpo_prompt("查询已支付订单", "orders(id,status)")
                + "\nSELECT id FROM orders WHERE status = 'cancelled'"
            ),
            "gold_sql": "SELECT id FROM orders WHERE status = 'paid'",
            "gold_result_signature": result_signature([{"id": 1}]),
            "reward_meta": {
                "required_tables": ["orders"],
                "non_empty_result": True,
                "preserve_result_order": False,
                "result_limit": 1000,
                "max_estimated_rows": 10_000_000,
            },
        }

        issues = validate_grpo_record(record)

        self.assertFalse(any("expose gold_sql" in issue.message for issue in issues))

    def test_gold_leak_ast_normalization_preserves_multitable_column_identity(self):
        gold_sql = (
            "SELECT a.id FROM orders AS a "
            "JOIN customers AS b ON a.customer_id = b.id"
        )
        equivalent = (
            "SELECT x.id FROM orders AS x "
            "JOIN customers AS y ON y.id = x.customer_id"
        )
        different_projection = (
            "SELECT y.id FROM orders AS x "
            "JOIN customers AS y ON y.id = x.customer_id"
        )

        self.assertTrue(_sql_leaks(equivalent, gold_sql, "sqlite"))
        self.assertFalse(_sql_leaks(different_projection, gold_sql, "sqlite"))

    def test_grpo_record_rejects_result_order_metadata_mismatch(self):
        record = {
            "id": "rl_001",
            "difficulty": "hard",
            "target_db": "local_sqlite",
            "dialect": "sqlite",
            "query": "按编号查询订单",
            "prompt": assemble_grpo_prompt("按编号查询订单", "schema"),
            "gold_sql": "SELECT id FROM orders ORDER BY id",
            "gold_result_signature": result_signature([{"id": 1}]),
            "reward_meta": {
                "required_tables": ["orders"],
                "non_empty_result": True,
                "preserve_result_order": False,
                "result_limit": 1000,
                "max_estimated_rows": 10_000_000,
            },
        }

        issues = validate_grpo_record(record)

        self.assertTrue(
            any(
                issue.field == "reward_meta.preserve_result_order"
                and "top-level ORDER BY" in issue.message
                for issue in issues
            )
        )

    def test_result_signature_preserves_order_by_default(self):
        first = [{"id": 1}, {"id": 2}]
        second = [{"id": 2}, {"id": 1}]

        self.assertNotEqual(result_signature(first), result_signature(second))
        self.assertEqual(
            result_signature(first, preserve_order=False),
            result_signature(second, preserve_order=False),
        )

    def test_validate_jsonl_reports_invalid_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sft.jsonl"
            write_jsonl(
                [
                    {
                        "instruction": "查询订单",
                        "input": "schema",
                        "output": "SELECT * FROM orders",
                    },
                    {
                        "instruction": "删除订单",
                        "input": "schema",
                        "output": "DELETE FROM orders",
                    },
                ],
                path,
            )

            report = validate_jsonl(path, "sft")

        self.assertEqual(report.total, 2)
        self.assertEqual(report.valid, 1)
        self.assertEqual(report.error_count, 1)

    def test_validate_jsonl_rejects_grpo_missing_online_prompt_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "grpo.jsonl"
            write_jsonl(
                [
                    {
                        "id": "rl_001",
                        "difficulty": "easy",
                        "target_db": "local_sqlite",
                        "dialect": "sqlite",
                        "query": "查询订单",
                        "prompt": "用户问题: 查询订单",
                        "gold_sql": "SELECT * FROM orders",
                        "gold_result_signature": result_signature([{"id": 1}]),
                        "reward_meta": {},
                    }
                ],
                path,
            )

            report = validate_jsonl(path, "grpo")

        self.assertEqual(report.total, 1)
        self.assertEqual(report.valid, 0)
        self.assertGreater(report.error_count, 0)

    def test_grpo_record_rejects_second_statement_after_select(self):
        record = {
            "id": "rl_001",
            "difficulty": "hard",
            "target_db": "local_sqlite",
            "dialect": "sqlite",
            "query": "查询订单",
            "prompt": assemble_grpo_prompt("查询订单", "schema"),
            "gold_sql": "SELECT * FROM orders; DROP TABLE orders",
            "gold_result_signature": result_signature([{"id": 1}]),
            "reward_meta": {},
        }

        issues = validate_grpo_record(record)

        self.assertTrue(any(issue.field == "gold_sql" for issue in issues))

    def test_grpo_record_rejects_invalid_ast_and_unsupported_dialect(self):
        record = {
            "id": "rl_001",
            "difficulty": "hard",
            "target_db": "warehouse",
            "dialect": "sqlserver",
            "query": "查询订单",
            "prompt": assemble_grpo_prompt("查询订单", "schema"),
            "gold_sql": "SELECT FROM orders",
            "gold_result_signature": result_signature([{"id": 1}]),
            "reward_meta": {
                "non_empty_result": True,
                "preserve_result_order": False,
                "result_limit": 1000,
                "max_estimated_rows": 10_000_000,
            },
        }

        issues = validate_grpo_record(record)

        self.assertTrue(any(issue.field == "dialect" for issue in issues))
        self.assertTrue(any(issue.field == "gold_sql" for issue in issues))
        self.assertEqual(strict_readonly_sql("EXPLAIN SELECT * FROM orders", "sqlite"), "")

    def test_grpo_record_rejects_non_sha256_signature(self):
        record = {
            "id": "rl_001",
            "difficulty": "hard",
            "target_db": "local_sqlite",
            "dialect": "sqlite",
            "query": "查询订单",
            "prompt": assemble_grpo_prompt("查询订单", "schema"),
            "gold_sql": "SELECT * FROM orders",
            "gold_result_signature": "abc",
            "reward_meta": {},
        }

        issues = validate_grpo_record(record)

        self.assertTrue(any(issue.field == "gold_result_signature" for issue in issues))

    def test_grpo_record_rejects_empty_gold_result_signature(self):
        record = {
            "id": "rl_001",
            "difficulty": "hard",
            "target_db": "local_sqlite",
            "dialect": "sqlite",
            "query": "查询不存在的订单",
            "prompt": assemble_grpo_prompt("查询不存在的订单", "schema"),
            "gold_sql": "SELECT * FROM orders WHERE 1 = 0",
            "gold_result_signature": result_signature([]),
            "reward_meta": {
                "non_empty_result": True,
                "preserve_result_order": False,
                "result_limit": 1000,
            },
        }

        issues = validate_grpo_record(record)

        self.assertTrue(any(issue.field == "gold_result_signature" for issue in issues))

    def test_grpo_record_rejects_required_table_mismatch(self):
        record = {
            "id": "rl_001",
            "difficulty": "hard",
            "target_db": "local_sqlite",
            "dialect": "sqlite",
            "query": "查询订单",
            "prompt": assemble_grpo_prompt("查询订单", "schema"),
            "gold_sql": "SELECT * FROM orders",
            "gold_result_signature": result_signature([{"id": 1}]),
            "reward_meta": {
                "required_tables": ["customers"],
                "non_empty_result": True,
                "preserve_result_order": False,
                "result_limit": 1000,
                "max_estimated_rows": 10_000_000,
            },
        }

        issues = validate_grpo_record(record)

        self.assertTrue(
            any(
                issue.field == "reward_meta.required_tables"
                and "customers" in issue.message
                for issue in issues
            )
        )

    def test_exports_valid_grpo_records_to_verl_parquet(self):
        record = {
            "id": "rl_001",
            "difficulty": "hard",
            "target_db": "local_sqlite",
            "dialect": "sqlite",
            "query": "查询订单",
            "prompt": assemble_grpo_prompt("查询订单", "schema"),
            "gold_sql": "SELECT * FROM orders",
            "gold_result_signature": result_signature([{"id": 1}]),
            "reward_meta": {
                "required_tables": ["orders"],
                "non_empty_result": True,
                "preserve_result_order": False,
                "result_limit": 1000,
                "max_estimated_rows": 10_000_000,
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "grpo.parquet"
            write_grpo_parquet([record], output)

            import pyarrow.parquet as pq

            exported = pq.read_table(output).to_pylist()

        self.assertEqual(exported[0]["data_source"], "text2sql")
        self.assertEqual(exported[0]["prompt"][0]["role"], "user")
        self.assertEqual(exported[0]["reward_model"]["ground_truth"], record["gold_sql"])
        self.assertEqual(exported[0]["extra_info"]["target_db"], "local_sqlite")

    def test_validate_jsonl_reports_non_object_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sft.jsonl"
            path.write_text("[]\n", encoding="utf-8")

            report = validate_jsonl(path, "sft")

        self.assertEqual(report.total, 1)
        self.assertEqual(report.valid, 0)
        self.assertTrue(any(issue.field == "$" for issue in report.issues))

    def test_grpo_gold_preflight_executes_and_verifies_signature(self):
        rows = [{"id": 1}, {"id": 2}]
        executor = FakeGoldExecutor(rows)
        record = {
            "id": "rl_001",
            "difficulty": "hard",
            "target_db": "local_sqlite",
            "dialect": "sqlite",
            "query": "查询订单",
            "prompt": assemble_grpo_prompt("查询订单", "schema"),
            "gold_sql": "SELECT id FROM orders ORDER BY id",
            "gold_result_signature": result_signature(rows, preserve_order=True),
            "reward_meta": {
                "required_tables": ["orders"],
                "non_empty_result": True,
                "preserve_result_order": True,
                "result_limit": 1000,
                "max_estimated_rows": 10_000_000,
            },
        }

        issues = validate_grpo_gold_record(
            record,
            sandbox_db_urls={"local_sqlite": "sqlite:///sandbox.sqlite"},
            redis_url="redis://127.0.0.1:6379/0",
            executor_factory=lambda **_: executor,
        )

        self.assertEqual(issues, [])
        self.assertEqual(
            executor.execute_calls,
            [(record["gold_sql"], "sqlite", 1001)],
        )

        overflow_record = dict(
            record,
            gold_result_signature=result_signature(rows[:1], preserve_order=True),
            reward_meta=dict(record["reward_meta"], result_limit=1),
        )
        overflow_issues = validate_grpo_gold_record(
            overflow_record,
            sandbox_db_urls={"local_sqlite": "sqlite:///sandbox.sqlite"},
            redis_url="redis://127.0.0.1:6379/0",
            executor_factory=lambda **_: FakeGoldExecutor(rows),
        )
        self.assertTrue(
            any(issue.field == "reward_meta.result_limit" for issue in overflow_issues)
        )

        mismatched = dict(record, gold_result_signature=result_signature([{"id": 9}]))
        mismatch_issues = validate_grpo_gold_record(
            mismatched,
            sandbox_db_urls={"local_sqlite": "sqlite:///sandbox.sqlite"},
            redis_url="redis://127.0.0.1:6379/0",
            executor_factory=lambda **_: executor,
        )
        self.assertTrue(
            any(issue.field == "gold_result_signature" for issue in mismatch_issues)
        )

        expensive_record = dict(
            record,
            reward_meta=dict(record["reward_meta"], max_estimated_rows=1),
        )
        cost_issues = validate_grpo_gold_record(
            expensive_record,
            sandbox_db_urls={"local_sqlite": "sqlite:///sandbox.sqlite"},
            redis_url="redis://127.0.0.1:6379/0",
            executor_factory=lambda **_: FakeGoldExecutor(rows, estimated_rows=2),
        )
        self.assertTrue(
            any(issue.field == "reward_meta.max_estimated_rows" for issue in cost_issues)
        )

    def test_split_records_deduplicates_then_keeps_templates_isolated(self):
        records = []
        for index in range(20):
            pair_index = index // 2
            record = {
                "id": f"rl_{index:03d}",
                "query_semantic_fingerprint": f"question_{index}",
                "sql_ast_fingerprint": f"ast_{index}",
                "schema_fingerprint": "shared_schema",
                "business_template_id": f"template_{pair_index}",
            }
            records.append(record)

        train, valid, test = split_records(records)

        template_locations = {}
        for split_name, split in (("train", train), ("valid", valid), ("test", test)):
            for record in split:
                template = record["business_template_id"]
                self.assertEqual(
                    template_locations.setdefault(template, split_name),
                    split_name,
                )
        self.assertEqual(len(train) + len(valid) + len(test), len(records))
        self.assertEqual((len(train), len(valid), len(test)), (16, 2, 2))
        self.assertEqual(
            {record["schema_fingerprint"] for record in train + valid + test},
            {"shared_schema"},
        )

    def test_split_records_removes_composite_fingerprint_duplicates(self):
        records = [
            {
                "id": f"rl_{index:03d}",
                "query_semantic_fingerprint": f"question_{index}",
                "sql_ast_fingerprint": f"ast_{index}",
                "schema_fingerprint": f"schema_{index}",
                "business_template_id": f"template_{index}",
            }
            for index in range(10)
        ]
        records.append(dict(records[0], id="duplicate"))

        train, valid, test = split_records(records)
        kept = train + valid + test

        self.assertEqual((len(train), len(valid), len(test)), (8, 1, 1))
        self.assertEqual(len(kept), 10)
        self.assertNotIn("duplicate", {record["id"] for record in kept})

    def test_split_records_rejects_unsplittable_template_groups(self):
        records = [
            {
                "id": f"rl_{index:03d}",
                "query_semantic_fingerprint": f"question_{index}",
                "sql_ast_fingerprint": f"ast_{index}",
                "schema_fingerprint": f"schema_{index}",
                "business_template_id": "one_template",
            }
            for index in range(10)
        ]

        with self.assertRaisesRegex(ValueError, "three template groups"):
            split_records(records)

    def test_split_records_requires_precomputed_fingerprints(self):
        with self.assertRaisesRegex(ValueError, "missing split fingerprints"):
            split_records([{"id": "rl_001", "query": "查询订单"}])


if __name__ == "__main__":
    unittest.main()
