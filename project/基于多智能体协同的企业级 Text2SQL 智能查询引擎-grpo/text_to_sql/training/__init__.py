"""Offline training helpers for the Text2SQL coder model."""

from .configs import build_lora_merge_config, init_training_artifacts
from .data import (
    DatasetValidationReport,
    SPLIT_FINGERPRINT_FIELDS,
    ValidationIssue,
    assemble_grpo_prompt,
    result_signature,
    split_records,
    to_verl_grpo_record,
    validate_grpo_gold_record,
    validate_grpo_jsonl_against_sandbox,
    validate_jsonl,
    write_grpo_parquet,
)
from .rewards import RewardResult, compute_grpo_reward, compute_score, format_verification_reward
from .quality import (
    fingerprint_sql_ast,
    validate_dataset_quality,
    validate_grpo_split,
    validate_supervised_jsonl_against_sandbox,
    validate_supervised_record_against_sandbox,
)

__all__ = [
    "DatasetValidationReport",
    "RewardResult",
    "SPLIT_FINGERPRINT_FIELDS",
    "ValidationIssue",
    "assemble_grpo_prompt",
    "build_lora_merge_config",
    "compute_grpo_reward",
    "compute_score",
    "format_verification_reward",
    "fingerprint_sql_ast",
    "init_training_artifacts",
    "result_signature",
    "split_records",
    "to_verl_grpo_record",
    "validate_grpo_gold_record",
    "validate_grpo_jsonl_against_sandbox",
    "validate_jsonl",
    "validate_dataset_quality",
    "validate_grpo_split",
    "validate_supervised_jsonl_against_sandbox",
    "validate_supervised_record_against_sandbox",
    "write_grpo_parquet",
]
