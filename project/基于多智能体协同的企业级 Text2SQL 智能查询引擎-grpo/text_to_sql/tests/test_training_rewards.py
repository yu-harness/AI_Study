import asyncio
import importlib.util
import inspect
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import text_to_sql.training.rewards as rewards_module
from text_to_sql.training.data import result_signature
from text_to_sql.training.rewards import (
    _has_top_level_order_by,
    _select_sandbox_route,
    _token_count,
    compute_grpo_reward,
    compute_score,
    format_verification_reward,
    qwen35_judge_reward,
)


class FakeRewardExecutor:
    def __init__(self):
        self.execute_calls = []

    def validate(self, sql, dialect="mysql"):
        return True, "", {"stage": "validated", "estimated_rows": 1}

    def execute(self, sql, dialect="mysql", limit=1000):
        self.execute_calls.append((sql, dialect, limit))
        if "DESC" in sql.upper() or "WHERE" in sql.upper():
            return {"success": True, "data": [{"id": 2}, {"id": 1}], "row_count": 2}
        return {"success": True, "data": [{"id": 1}, {"id": 2}], "row_count": 2}


class HighCostRewardExecutor:
    def validate(self, sql, dialect="mysql"):
        return False, "estimated rows exceed threshold", {
            "stage": "cost",
            "estimated_rows": 20_000_000,
        }

    def execute(self, sql, dialect="mysql", limit=1000):
        raise AssertionError("high-cost SQL must not execute")


class TestTrainingRewards(unittest.TestCase):
    def test_reward_module_loads_from_file_path_like_verl(self):
        module_name = "_text2sql_verl_reward_test"
        spec = importlib.util.spec_from_file_location(
            module_name,
            Path(rewards_module.__file__),
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        finally:
            del sys.modules[module_name]

        self.assertTrue(callable(module.compute_score))
        self.assertTrue(inspect.iscoroutinefunction(module.compute_score))

    def test_format_reward_rejects_pure_sql_for_grpo(self):
        reward = format_verification_reward(
            "SELECT * FROM orders",
            token_counter=lambda _: 50,
        )

        self.assertEqual(reward, 0.0)

    def test_format_reward_rejects_markdown(self):
        self.assertEqual(format_verification_reward("```sql\nSELECT * FROM orders\n```"), 0.0)

    def test_format_reward_rejects_prose_after_sql(self):
        self.assertEqual(format_verification_reward("SELECT * FROM orders\n这里是解释"), 0.0)

    def test_format_reward_penalizes_short_think(self):
        output = "<think>太短</think>\nSELECT * FROM orders"
        self.assertEqual(format_verification_reward(output), 0.5)

    def test_format_reward_penalizes_short_pure_sql(self):
        self.assertEqual(format_verification_reward("SELECT * FROM orders"), 0.0)

    def test_format_reward_rejects_empty_think(self):
        output = "<think>  </think>\nSELECT * FROM orders"
        self.assertEqual(format_verification_reward(output), 0.0)

    def test_format_reward_rejects_write_cte(self):
        output = "WITH deleted AS (DELETE FROM orders RETURNING *) SELECT * FROM deleted"

        self.assertEqual(format_verification_reward(output), 0.0)

    def test_chinese_token_counter_does_not_collapse_text_to_one_token(self):
        self.assertEqual(_token_count("汉字" * 60), 120)

    def test_compute_grpo_reward_without_executor_fails_fast(self):
        with self.assertRaisesRegex(ValueError, "sandbox executor"):
            compute_grpo_reward(
                "SELECT * FROM orders",
                {"id": "rl_001", "dialect": "sqlite", "reward_meta": {}},
                executor=None,
                judge_score=0.5,
            )

    def test_qwen_judge_rejects_non_loopback_url(self):
        with self.assertRaisesRegex(ValueError, "loopback-only"):
            qwen35_judge_reward(
                query="查询订单",
                candidate_sql="SELECT * FROM orders",
                gold_sql="SELECT * FROM orders",
                prompt_context="schema",
                required_tables=["orders"],
                base_url="https://example.com",
            )

    @patch("text_to_sql.training.rewards._build_local_judge")
    def test_qwen_judge_parses_structured_local_score(self, build_judge):
        generation = MagicMock()
        generation.outputs[0].text = '{"score": 0.75}'
        build_judge.return_value.generate.return_value = [generation]

        score = qwen35_judge_reward(
            query="查询订单",
            candidate_sql="SELECT * FROM orders",
            gold_sql="SELECT * FROM orders",
            prompt_context="schema",
            required_tables=["orders"],
            base_url="http://127.0.0.1:8000",
        )

        self.assertEqual(score, 0.75)
        params = build_judge.return_value.generate.call_args.args[1]
        self.assertEqual(params.format["required"], ["score"])

    def test_compute_grpo_reward_uses_precomputed_signature_without_running_gold(self):
        executor = FakeRewardExecutor()
        reward = compute_grpo_reward(
            "SELECT id FROM orders ORDER BY id",
            {
                "id": "rl_001",
                "dialect": "sqlite",
                "gold_sql": "SELECT id FROM orders ORDER BY id",
                "gold_result_signature": result_signature([{"id": 1}, {"id": 2}]),
                "reward_meta": {
                    "required_tables": ["orders"],
                    "non_empty_result": True,
                    "preserve_result_order": True,
                    "result_limit": 2,
                    "max_estimated_rows": 10_000_000,
                },
            },
            executor=executor,
        )

        self.assertEqual(reward.execution_reward, 1.0)
        self.assertEqual(
            reward.details["expected_signature_source"],
            "gold_result_signature",
        )
        self.assertEqual(len(executor.execute_calls), 1)
        self.assertEqual(executor.execute_calls[0][2], 3)

    def test_candidate_exceeding_result_limit_cannot_match_truncated_gold(self):
        executor = FakeRewardExecutor()
        reward = compute_grpo_reward(
            "<think>读取全部订单编号。</think>\nSELECT id FROM orders ORDER BY id",
            {
                "id": "rl_001",
                "dialect": "sqlite",
                "gold_sql": "SELECT id FROM orders ORDER BY id LIMIT 1",
                "gold_result_signature": result_signature([{"id": 1}]),
                "reward_meta": {
                    "required_tables": ["orders"],
                    "non_empty_result": True,
                    "preserve_result_order": True,
                    "result_limit": 1,
                    "max_estimated_rows": 10_000_000,
                },
            },
            executor=executor,
            token_counter=lambda _: 100,
        )

        self.assertEqual(reward.execution_reward, 0.0)
        self.assertEqual(reward.penalty, 0.5)
        self.assertTrue(reward.details["result_limit_exceeded"])
        self.assertEqual(executor.execute_calls[0][2], 2)

    def test_compute_grpo_reward_preserves_order_by_default(self):
        reward = compute_grpo_reward(
            "SELECT id FROM orders ORDER BY id DESC",
            {
                "id": "rl_001",
                "dialect": "sqlite",
                "gold_sql": "SELECT id FROM orders ORDER BY id",
                "gold_result_signature": result_signature([{"id": 1}, {"id": 2}]),
                "reward_meta": {
                    "required_tables": ["orders"],
                    "non_empty_result": True,
                    "preserve_result_order": True,
                    "result_limit": 1000,
                    "max_estimated_rows": 10_000_000,
                },
            },
            executor=FakeRewardExecutor(),
        )

        self.assertEqual(reward.execution_reward, 0.0)

    def test_compute_grpo_reward_rejects_result_order_metadata_mismatch(self):
        with self.assertRaisesRegex(ValueError, "top-level ORDER BY"):
            compute_grpo_reward(
                "SELECT id FROM orders ORDER BY id",
                {
                    "id": "rl_001",
                    "dialect": "sqlite",
                    "gold_sql": "SELECT id FROM orders ORDER BY id",
                    "gold_result_signature": result_signature([{"id": 1}, {"id": 2}]),
                    "reward_meta": {
                        "required_tables": ["orders"],
                        "non_empty_result": True,
                        "preserve_result_order": False,
                        "result_limit": 1000,
                        "max_estimated_rows": 10_000_000,
                    },
                },
                executor=FakeRewardExecutor(),
            )

    def test_compute_grpo_reward_ignores_order_without_order_by(self):
        reward = compute_grpo_reward(
            "<think>筛选有效订单并返回编号。</think>\nSELECT id FROM orders WHERE id > 0",
            {
                "id": "rl_001",
                "dialect": "sqlite",
                "gold_sql": "SELECT id FROM orders",
                "gold_result_signature": result_signature(
                    [{"id": 1}, {"id": 2}],
                    preserve_order=False,
                ),
                "reward_meta": {
                    "required_tables": ["orders"],
                    "non_empty_result": True,
                    "preserve_result_order": False,
                    "result_limit": 1000,
                    "max_estimated_rows": 10_000_000,
                },
            },
            executor=FakeRewardExecutor(),
            token_counter=lambda _: 100,
        )

        self.assertEqual(reward.execution_reward, 1.0)
        self.assertFalse(reward.details["preserve_result_order"])

    def test_execution_metric_stays_binary_when_judge_scores_vary(self):
        sample = {
            "id": "rl_001",
            "dialect": "sqlite",
            "gold_sql": "SELECT id FROM orders",
            "gold_result_signature": result_signature([{"id": 9}]),
            "reward_meta": {
                "required_tables": ["orders"],
                "non_empty_result": True,
                "preserve_result_order": False,
                "result_limit": 1000,
                "max_estimated_rows": 10_000_000,
            },
        }
        output = (
            "<think>读取订单编号并返回结果。</think>\n"
            "SELECT id FROM orders WHERE id > 0"
        )

        low_judge = compute_grpo_reward(
            output,
            sample,
            executor=FakeRewardExecutor(),
            judge_score=0.0,
            token_counter=lambda _: 100,
        ).to_metrics()
        high_judge = compute_grpo_reward(
            output,
            sample,
            executor=FakeRewardExecutor(),
            judge_score=1.0,
            token_counter=lambda _: 100,
        ).to_metrics()

        self.assertNotEqual(low_judge["score"], high_judge["score"])
        self.assertEqual(low_judge["execution_correct"], 0.0)
        self.assertEqual(high_judge["execution_correct"], 0.0)

    def test_window_order_by_is_not_top_level_result_order(self):
        sql = "SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS row_num FROM orders"

        self.assertFalse(_has_top_level_order_by(sql, "sqlite"))
        self.assertTrue(
            _has_top_level_order_by(f"{sql} ORDER BY row_num", "sqlite")
        )

    def test_empty_gold_signature_fails_fast(self):
        with self.assertRaisesRegex(ValueError, "non-empty result"):
            compute_grpo_reward(
                "SELECT id FROM orders WHERE 1 = 0",
                {
                    "id": "rl_001",
                    "dialect": "sqlite",
                    "gold_sql": "SELECT id FROM orders WHERE 1 = 0",
                    "gold_result_signature": result_signature([]),
                    "reward_meta": {
                        "required_tables": ["orders"],
                        "non_empty_result": True,
                        "preserve_result_order": False,
                        "result_limit": 1000,
                        "max_estimated_rows": 10_000_000,
                    },
                },
                executor=FakeRewardExecutor(),
            )

    def test_high_cost_validation_applies_penalty_and_skips_execution(self):
        reward = compute_grpo_reward(
            "<think>扫描订单用于聚合分析。</think>\nSELECT * FROM orders",
            {
                "id": "rl_001",
                "dialect": "mysql",
                "gold_sql": "SELECT * FROM orders",
                "gold_result_signature": result_signature([{"id": 1}]),
                "reward_meta": {
                    "required_tables": ["orders"],
                    "non_empty_result": True,
                    "preserve_result_order": False,
                    "result_limit": 1000,
                    "max_estimated_rows": 10_000_000,
                },
            },
            executor=HighCostRewardExecutor(),
            judge_score=1.0,
            token_counter=lambda _: 100,
        )

        self.assertEqual(reward.execution_reward, 0.0)
        self.assertEqual(reward.penalty, 0.5)
        self.assertEqual(reward.total, -0.3)

    def test_sandbox_url_routes_by_target_database(self):
        routes = '{"docker_postgres":"postgresql://db/train","local_sqlite":"sqlite:///train.db"}'

        self.assertEqual(
            _select_sandbox_route(routes, "local_sqlite"),
            ("sqlite:///train.db", "sqlite"),
        )
        self.assertEqual(
            _select_sandbox_route(routes, "docker_postgres"),
            ("postgresql://db/train", "postgresql"),
        )
        with self.assertRaisesRegex(ValueError, "target_db=missing"):
            _select_sandbox_route(routes, "missing")

    def test_verl_compute_score_rejects_dialect_route_mismatch(self):
        sample = {
            "id": "rl_001",
            "target_db": "local_sqlite",
            "dialect": "mysql",
            "query": "查询订单",
            "prompt": "schema",
            "gold_sql": "SELECT id FROM orders",
            "gold_result_signature": result_signature([{"id": 1}]),
            "reward_meta": {
                "required_tables": ["orders"],
                "non_empty_result": True,
                "preserve_result_order": False,
                "result_limit": 1000,
                "max_estimated_rows": 10_000_000,
            },
        }

        with self.assertRaisesRegex(ValueError, "does not match target_db route"):
            asyncio.run(
                compute_score(
                    data_source="text2sql",
                    solution_str="SELECT id FROM orders",
                    ground_truth=sample["gold_sql"],
                    extra_info=sample,
                    sandbox_db_urls={"local_sqlite": "sqlite:///sandbox.sqlite"},
                    redis_url="redis://127.0.0.1:6379/0",
                    judge_base_url="http://127.0.0.1:8000",
                    tokenizer_path="models/dpo_merged",
                )
            )

    @patch("text_to_sql.training.rewards.qwen35_judge_reward", return_value=1.0)
    @patch("text_to_sql.training.rewards._token_count", return_value=100)
    @patch("text_to_sql.training.rewards._build_executor")
    def test_verl_compute_score_uses_sandbox_and_local_judge(
        self,
        build_executor,
        _token_count_mock,
        judge_reward,
    ):
        build_executor.return_value = FakeRewardExecutor()
        sample = {
            "id": "rl_001",
            "target_db": "local_sqlite",
            "dialect": "sqlite",
            "query": "查询订单",
            "prompt": "schema",
            "gold_sql": "SELECT id FROM orders ORDER BY id",
            "gold_result_signature": result_signature([{"id": 1}, {"id": 2}]),
            "reward_meta": {
                "required_tables": ["orders"],
                "non_empty_result": True,
                "preserve_result_order": True,
                "result_limit": 1000,
                "max_estimated_rows": 10_000_000,
            },
        }

        score = asyncio.run(
            compute_score(
                data_source="text2sql",
                solution_str=(
                    "<think>按编号稳定排序后返回订单。</think>\n"
                    "SELECT id FROM orders ORDER BY id"
                ),
                ground_truth=sample["gold_sql"],
                extra_info=sample,
                sandbox_db_urls={"local_sqlite": "sqlite:///sandbox.sqlite"},
                redis_url="redis://127.0.0.1:6379/0",
                judge_base_url="http://127.0.0.1:8000",
                tokenizer_path="models/dpo_merged",
            )
        )

        self.assertEqual(
            score,
            {
                "score": 1.2,
                "format_reward": 1.0,
                "execution_reward": 1.0,
                "execution_correct": 1.0,
                "judge_reward": 1.0,
                "penalty": 0.0,
            },
        )
        self.assertEqual(
            build_executor.call_args.kwargs["sandbox_db_url"],
            "sqlite:///sandbox.sqlite",
        )
        self.assertEqual(judge_reward.call_args.kwargs["required_tables"], ["orders"])


if __name__ == "__main__":
    unittest.main()
