import hashlib
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from text_to_sql.training.cli import SUPERVISED_SOURCE_MINIMUMS, main
from text_to_sql.training.data import DatasetValidationReport


class TestTrainingCli(unittest.TestCase):
    def test_supervised_source_minimums_preserve_documented_training_counts(self):
        self.assertEqual(SUPERVISED_SOURCE_MINIMUMS["sft"], 77_778)
        self.assertEqual(SUPERVISED_SOURCE_MINIMUMS["dpo"], 22_223)
        self.assertGreaterEqual(77_778 - 7_778, 70_000)
        self.assertGreaterEqual(22_223 - 2_223, 20_000)

    def test_export_grpo_requires_sandbox_configuration(self):
        stderr = io.StringIO()
        with patch.dict(
            os.environ,
            {"TEXT2SQL_TRAINING_DB_URLS": "", "TEXT2SQL_REDIS_URL": ""},
        ), redirect_stderr(stderr):
            exit_code = main(["export-grpo", "input.jsonl", "--output", "output.parquet"])

        self.assertEqual(exit_code, 2)
        self.assertIn("requires --db-urls", stderr.getvalue())

    def test_quality_gate_requires_sandbox_configuration(self):
        stderr = io.StringIO()
        with patch.dict(
            os.environ,
            {"TEXT2SQL_TRAINING_DB_URLS": "", "TEXT2SQL_REDIS_URL": ""},
        ), redirect_stderr(stderr):
            exit_code = main(
                [
                    "quality-gate",
                    "grpo",
                    "input.jsonl",
                    "--sensitive-fields",
                    "sensitive-fields.json",
                ]
            )

        self.assertEqual(exit_code, 2)
        self.assertIn("quality-gate requires --db-urls", stderr.getvalue())

    def test_sft_quality_gate_requires_evaluation_dataset(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = main(
                [
                    "quality-gate",
                    "sft",
                    "input.jsonl",
                    "--sensitive-fields",
                    "sensitive-fields.json",
                    "--db-urls",
                    '{"local_sqlite":"sqlite:///sandbox.sqlite"}',
                    "--redis-url",
                    "redis://127.0.0.1:6379/0",
                ]
            )

        self.assertEqual(exit_code, 2)
        self.assertIn("requires --eval-path", stderr.getvalue())

    def test_sft_quality_gate_requires_fixed_evaluation_sha256(self):
        stderr = io.StringIO()
        with patch.dict(os.environ, {"TEXT2SQL_EVAL_SHA256": ""}), redirect_stderr(stderr):
            exit_code = main(
                [
                    "quality-gate",
                    "sft",
                    "input.jsonl",
                    "--eval-path",
                    "evaluation.jsonl",
                    "--sensitive-fields",
                    "sensitive-fields.json",
                    "--db-urls",
                    '{"local_sqlite":"sqlite:///sandbox.sqlite"}',
                    "--redis-url",
                    "redis://127.0.0.1:6379/0",
                ]
            )

        self.assertEqual(exit_code, 2)
        self.assertIn("requires --eval-sha256", stderr.getvalue())

    def test_sft_quality_gate_rejects_evaluation_sha256_mismatch(self):
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            evaluation_path = Path(tmp) / "evaluation.jsonl"
            evaluation_path.write_text("{}\n", encoding="utf-8")
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        "quality-gate",
                        "sft",
                        "input.jsonl",
                        "--eval-path",
                        str(evaluation_path),
                        "--eval-sha256",
                        "0" * 64,
                        "--sensitive-fields",
                        "sensitive-fields.json",
                        "--db-urls",
                        '{"local_sqlite":"sqlite:///sandbox.sqlite"}',
                        "--redis-url",
                        "redis://127.0.0.1:6379/0",
                    ]
                )

        self.assertEqual(exit_code, 2)
        self.assertIn("SHA256 mismatch", stderr.getvalue())

    @patch("text_to_sql.training.cli._print_report")
    @patch("text_to_sql.training.cli.validate_dataset_quality", return_value=[])
    @patch(
        "text_to_sql.training.cli.read_jsonl",
        side_effect=[[{"id": "eval"}], [{"id": "train"}]],
    )
    @patch("text_to_sql.training.cli.validate_supervised_jsonl_against_sandbox")
    def test_sft_quality_gate_accepts_governed_evaluation_sha256(
        self,
        validate_against_sandbox,
        read_jsonl,
        validate_quality,
        _print_report,
    ):
        validate_against_sandbox.return_value = DatasetValidationReport(
            kind="sft",
            path="input.jsonl",
            total=1,
            valid=1,
        )
        with tempfile.TemporaryDirectory() as tmp:
            evaluation_path = Path(tmp) / "evaluation.jsonl"
            evaluation_path.write_text("{}\n", encoding="utf-8")
            sensitive_path = Path(tmp) / "sensitive.json"
            sensitive_path.write_text('["password"]', encoding="utf-8")
            evaluation_sha256 = hashlib.sha256(evaluation_path.read_bytes()).hexdigest()

            exit_code = main(
                [
                    "quality-gate",
                    "sft",
                    "input.jsonl",
                    "--eval-path",
                    str(evaluation_path),
                    "--eval-sha256",
                    evaluation_sha256,
                    "--sensitive-fields",
                    str(sensitive_path),
                    "--db-urls",
                    '{"local_sqlite":"sqlite:///sandbox.sqlite"}',
                    "--redis-url",
                    "redis://127.0.0.1:6379/0",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(read_jsonl.call_count, 2)
        self.assertEqual(read_jsonl.call_args_list[0].args[0], str(evaluation_path))
        validate_quality.assert_called_once()
        _print_report.assert_called_once()

    @patch("text_to_sql.training.cli.write_jsonl")
    @patch(
        "text_to_sql.training.cli.split_records",
        return_value=([{"id": "train"}], [{"id": "valid"}], [{"id": "holdout"}]),
    )
    @patch("text_to_sql.training.cli.read_jsonl", return_value=[{"id": "source"}])
    def test_split_writes_holdout_name(self, read_jsonl, split_records, write_jsonl):
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main(
                ["split", "input.jsonl", "--output", "artifacts", "--prefix", "rl"]
            )

        self.assertEqual(exit_code, 0)
        read_jsonl.assert_called_once_with("input.jsonl")
        split_records.assert_called_once_with([{"id": "source"}], seed=2025, group_key=None)
        self.assertEqual(write_jsonl.call_args_list[2].args[1].name, "rl_holdout.jsonl")
        self.assertIn("holdout=1", stdout.getvalue())

    @patch("text_to_sql.training.cli.write_grpo_parquet")
    @patch("text_to_sql.training.cli.read_jsonl", return_value=[{"id": "rl_001"}])
    @patch("text_to_sql.training.cli.validate_grpo_jsonl_against_sandbox")
    def test_export_grpo_runs_gold_preflight_before_writing(
        self,
        validate_against_sandbox,
        read_jsonl,
        write_grpo_parquet,
    ):
        validate_against_sandbox.return_value = Mock(is_valid=True)
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "export-grpo",
                    "input.jsonl",
                    "--output",
                    "output.parquet",
                    "--db-urls",
                    '{"local_sqlite":"sqlite:///sandbox.sqlite"}',
                    "--redis-url",
                    "redis://127.0.0.1:6379/0",
                    "--query-timeout",
                    "7",
                    "--cost-threshold-rows",
                    "1234",
                ]
            )

        self.assertEqual(exit_code, 0)
        validate_against_sandbox.assert_called_once_with(
            "input.jsonl",
            sandbox_db_urls='{"local_sqlite":"sqlite:///sandbox.sqlite"}',
            redis_url="redis://127.0.0.1:6379/0",
            query_timeout=7,
            cost_threshold_rows=1234,
        )
        read_jsonl.assert_called_once_with("input.jsonl")
        write_grpo_parquet.assert_called_once_with(
            [{"id": "rl_001"}],
            "output.parquet",
        )


if __name__ == "__main__":
    unittest.main()
