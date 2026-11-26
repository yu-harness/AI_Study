"""Command line tools for Text2SQL offline training preparation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from .configs import init_training_artifacts
from .data import (
    DatasetValidationReport,
    read_jsonl,
    split_records,
    validate_grpo_jsonl_against_sandbox,
    validate_jsonl,
    write_grpo_parquet,
    write_jsonl,
)
from .quality import (
    GRPO_DIFFICULTY_TARGETS,
    SFT_DIFFICULTY_TARGETS,
    validate_dataset_quality,
    validate_grpo_split,
    validate_supervised_jsonl_against_sandbox,
)


SUPERVISED_SOURCE_MINIMUMS = {
    # LlamaFactory reserves 10% through val_size, leaving the documented
    # 70K SFT samples and 20K DPO pairs for optimizer updates.
    "sft": 77_778,
    "dpo": 22_223,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Text2SQL training utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init",
        help="write SFT/DPO/merge/GRPO config templates",
    )
    init_parser.add_argument("--output", default="training_artifacts", help="artifact directory")
    init_parser.add_argument("--sft-model", default="Qwen/Qwen2.5-Coder-14B")
    init_parser.add_argument("--sft-checkpoint", default="models/sft_qwen2.5_coder_14b")
    init_parser.add_argument(
        "--merged-sft-model",
        default="models/sft_qwen2.5_coder_14b_merged",
    )
    init_parser.add_argument("--dpo-checkpoint", default="models/dpo_qwen2.5_coder_14b")
    init_parser.add_argument(
        "--merged-dpo-model",
        default="models/dpo_qwen2.5_coder_14b_merged",
    )

    validate_parser = subparsers.add_parser("validate", help="validate a JSONL dataset")
    validate_parser.add_argument("kind", choices=["sft", "dpo", "grpo"])
    validate_parser.add_argument("path")
    validate_parser.add_argument("--json", action="store_true", help="print machine-readable report")

    split_parser = subparsers.add_parser(
        "split",
        help="split a JSONL dataset into train/valid/holdout",
    )
    split_parser.add_argument("path")
    split_parser.add_argument("--output", required=True)
    split_parser.add_argument("--seed", type=int, default=2025)
    split_parser.add_argument(
        "--group-key",
        default=None,
        help="explicit legacy group field; default deduplicates fingerprints and groups templates",
    )
    split_parser.add_argument("--prefix", default="text2sql_rl")

    export_parser = subparsers.add_parser(
        "export-grpo",
        help="validate GRPO JSONL and export veRL-compatible Parquet",
    )
    export_parser.add_argument("path")
    export_parser.add_argument("--output", required=True)
    export_parser.add_argument(
        "--db-urls",
        default=os.environ.get("TEXT2SQL_TRAINING_DB_URLS"),
        help="target_db to sandbox URL JSON; defaults to TEXT2SQL_TRAINING_DB_URLS",
    )
    export_parser.add_argument(
        "--redis-url",
        default=os.environ.get("TEXT2SQL_REDIS_URL"),
        help="sandbox Redis URL; defaults to TEXT2SQL_REDIS_URL",
    )
    export_parser.add_argument("--query-timeout", type=int, default=5)
    export_parser.add_argument("--cost-threshold-rows", type=int, default=10_000_000)

    quality_parser = subparsers.add_parser(
        "quality-gate",
        help="run final data admission gates, including sandbox execution",
    )
    quality_parser.add_argument("kind", choices=["sft", "dpo", "grpo"])
    quality_parser.add_argument("path")
    quality_parser.add_argument("--eval-path")
    quality_parser.add_argument(
        "--sensitive-fields",
        required=True,
        help="UTF-8 JSON file containing an array of sensitive column names",
    )
    quality_parser.add_argument(
        "--db-urls",
        default=os.environ.get("TEXT2SQL_TRAINING_DB_URLS"),
    )
    quality_parser.add_argument(
        "--redis-url",
        default=os.environ.get("TEXT2SQL_REDIS_URL"),
    )
    quality_parser.add_argument("--query-timeout", type=int, default=5)
    quality_parser.add_argument("--cost-threshold-rows", type=int, default=10_000_000)
    quality_parser.add_argument("--difficulty-tolerance", type=float, default=0.02)
    quality_parser.add_argument("--similarity-threshold", type=float, default=0.92)
    quality_parser.add_argument(
        "--eval-sha256",
        default=os.environ.get("TEXT2SQL_EVAL_SHA256"),
        help="governed SHA256 of the fixed 2,500-row evaluation JSONL",
    )
    quality_parser.add_argument("--json", action="store_true")

    split_gate_parser = subparsers.add_parser(
        "quality-gate-grpo-split",
        help="enforce the final 8K/1K/1K GRPO split",
    )
    split_gate_parser.add_argument("--train", required=True)
    split_gate_parser.add_argument("--valid", required=True)
    split_gate_parser.add_argument("--holdout", required=True)
    split_gate_parser.add_argument("--difficulty-tolerance", type=float, default=0.02)
    split_gate_parser.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "init":
        paths = init_training_artifacts(
            output_dir=args.output,
            sft_model=args.sft_model,
            sft_checkpoint=args.sft_checkpoint,
            merged_sft_model=args.merged_sft_model,
            dpo_checkpoint=args.dpo_checkpoint,
            merged_dpo_model=args.merged_dpo_model,
        )
        for name, path in paths.items():
            print(f"{name}: {path}")
        artifact_root = Path(args.output).resolve()
        config_root = (artifact_root / "configs").as_posix()
        project_root = Path(__file__).resolve().parents[2]
        reward_path = (project_root / "text_to_sql" / "training" / "rewards.py").resolve()
        replay_buffer_path = (
            project_root / "text_to_sql" / "training" / "verl_sampler.py"
        ).resolve()
        print(f"\nRun the following commands from: {artifact_root}")
        print(f"Add this project root to PYTHONPATH for GRPO: {project_root}")
        print(f"Set TEXT2SQL_REWARD_PATH={reward_path}")
        print(f"Set TEXT2SQL_REPLAY_BUFFER_PATH={replay_buffer_path}")
        print(
            "Set TEXT2SQL_SFT_BACKFLOW_PATH="
            f"{(artifact_root / 'backflow' / 'sft_groups.jsonl').resolve()}"
        )
        print(
            "Set TEXT2SQL_BAD_CASE_BACKFLOW_PATH="
            f"{(artifact_root / 'backflow' / 'bad_case_groups.jsonl').resolve()}"
        )
        print(f'SFT: llamafactory-cli train "{config_root}/sft_qwen.yaml"')
        print(f'Merge SFT: llamafactory-cli export "{config_root}/merge_sft_qwen.yaml"')
        print(f'DPO: llamafactory-cli train "{config_root}/dpo_qwen.yaml"')
        print(f'Merge DPO: llamafactory-cli export "{config_root}/merge_dpo_qwen.yaml"')
        print(
            "GRPO: python -m verl.trainer.main_ppo "
            f'--config-path="{config_root}" --config-name=grpo_text2sql'
        )
        return 0

    if args.command == "validate":
        report = validate_jsonl(args.path, args.kind)
        _print_report(report, args.json)
        return 0 if report.is_valid else 1

    if args.command == "split":
        records = read_jsonl(args.path)
        train, valid, holdout = split_records(records, seed=args.seed, group_key=args.group_key)
        output = Path(args.output)
        write_jsonl(train, output / f"{args.prefix}_train.jsonl")
        write_jsonl(valid, output / f"{args.prefix}_valid.jsonl")
        write_jsonl(holdout, output / f"{args.prefix}_holdout.jsonl")
        kept = len(train) + len(valid) + len(holdout)
        print(
            f"train={len(train)} valid={len(valid)} holdout={len(holdout)} "
            f"duplicates_removed={len(records) - kept}"
        )
        return 0

    if args.command == "export-grpo":
        if not args.db_urls or not args.redis_url:
            print(
                "export-grpo requires --db-urls/TEXT2SQL_TRAINING_DB_URLS and "
                "--redis-url/TEXT2SQL_REDIS_URL",
                file=sys.stderr,
            )
            return 2
        report = validate_grpo_jsonl_against_sandbox(
            args.path,
            sandbox_db_urls=args.db_urls,
            redis_url=args.redis_url,
            query_timeout=args.query_timeout,
            cost_threshold_rows=args.cost_threshold_rows,
        )
        if not report.is_valid:
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
            return 1
        records = read_jsonl(args.path)
        write_grpo_parquet(records, args.output)
        print(f"exported={len(records)} output={Path(args.output)}")
        return 0

    if args.command == "quality-gate":
        evaluation_records = None
        if not args.db_urls or not args.redis_url:
            print(
                "quality-gate requires --db-urls/TEXT2SQL_TRAINING_DB_URLS and "
                "--redis-url/TEXT2SQL_REDIS_URL",
                file=sys.stderr,
            )
            return 2
        if args.kind == "sft" and not args.eval_path:
            print("SFT quality-gate requires --eval-path for the 0.92 leakage gate", file=sys.stderr)
            return 2
        if args.kind == "sft" and not args.eval_sha256:
            print(
                "SFT quality-gate requires --eval-sha256/TEXT2SQL_EVAL_SHA256 "
                "to lock the fixed evaluation dataset",
                file=sys.stderr,
            )
            return 2
        if args.kind == "sft":
            expected_eval_sha256 = str(args.eval_sha256).strip().lower()
            actual_eval_sha256 = hashlib.sha256(Path(args.eval_path).read_bytes()).hexdigest()
            if expected_eval_sha256 != actual_eval_sha256:
                print(
                    "SFT evaluation dataset SHA256 mismatch: "
                    f"expected={expected_eval_sha256}, actual={actual_eval_sha256}",
                    file=sys.stderr,
                )
                return 2
            evaluation_records = read_jsonl(args.eval_path)

        sensitive_fields = _read_sensitive_fields(args.sensitive_fields)
        if args.kind in {"sft", "dpo"}:
            report = validate_supervised_jsonl_against_sandbox(
                args.path,
                args.kind,
                sandbox_db_urls=args.db_urls,
                redis_url=args.redis_url,
                sensitive_fields=sensitive_fields,
                query_timeout=args.query_timeout,
                cost_threshold_rows=args.cost_threshold_rows,
            )
        else:
            report = validate_grpo_jsonl_against_sandbox(
                args.path,
                sandbox_db_urls=args.db_urls,
                redis_url=args.redis_url,
                query_timeout=args.query_timeout,
                cost_threshold_rows=args.cost_threshold_rows,
            )
        if report.is_valid:
            records = read_jsonl(args.path)
            quality_issues = validate_dataset_quality(
                records,
                args.kind,
                expected_total=10_000 if args.kind == "grpo" else None,
                minimum_total=SUPERVISED_SOURCE_MINIMUMS.get(args.kind),
                difficulty_targets={
                    "sft": SFT_DIFFICULTY_TARGETS,
                    "grpo": GRPO_DIFFICULTY_TARGETS,
                }.get(args.kind),
                difficulty_tolerance=args.difficulty_tolerance,
                sensitive_fields=sensitive_fields,
                evaluation_records=evaluation_records,
                similarity_threshold=args.similarity_threshold,
            )
            report.issues.extend(quality_issues)
            invalid_lines = {issue.line for issue in quality_issues if issue.line > 0}
            report.valid = 0 if any(issue.line == 0 for issue in quality_issues) else report.total - len(invalid_lines)
        _print_report(report, args.json)
        return 0 if report.is_valid else 1

    if args.command == "quality-gate-grpo-split":
        train = read_jsonl(args.train)
        valid = read_jsonl(args.valid)
        holdout = read_jsonl(args.holdout)
        issues = validate_grpo_split(
            train,
            valid,
            holdout,
            difficulty_tolerance=args.difficulty_tolerance,
        )
        total = len(train) + len(valid) + len(holdout)
        report = DatasetValidationReport(
            kind="grpo_split",
            path=f"{args.train}|{args.valid}|{args.holdout}",
            total=total,
            valid=total if not issues else 0,
            issues=issues,
        )
        _print_report(report, args.json)
        return 0 if report.is_valid else 1

    return 2


def _read_sensitive_fields(path: str | Path) -> list[str]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data or any(
        not isinstance(field, str) or not field.strip() for field in data
    ):
        raise ValueError("sensitive-fields file must be a non-empty JSON array of non-empty strings")
    return data


def _print_report(report: DatasetValidationReport, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return
    print(
        f"{report.kind} validation: total={report.total}, valid={report.valid}, "
        f"errors={report.error_count}, warnings={report.warning_count}"
    )
    for issue in report.issues[:50]:
        print(f"line {issue.line} [{issue.severity}] {issue.field}: {issue.message}")
    if len(report.issues) > 50:
        print(f"... {len(report.issues) - 50} more issues")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
