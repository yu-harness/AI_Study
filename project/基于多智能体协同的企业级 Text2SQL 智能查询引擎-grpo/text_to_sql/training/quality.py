"""Final data-quality gates for Text2SQL training datasets."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
from sqlglot import exp, parse_one

from text_to_sql.training.data import (
    DatasetValidationReport,
    SPLIT_FINGERPRINT_FIELDS,
    ValidationIssue,
    has_top_level_order_by,
    read_jsonl,
    result_signature,
    strict_readonly_sql,
    validate_dpo_record,
    validate_jsonl,
    validate_sft_record,
)
from text_to_sql.training.sandbox_routes import (
    build_training_executor,
    normalize_database_dialect,
    select_sandbox_route,
    sqlglot_dialect,
)


SHA256_PATTERN = re.compile(r"[0-9a-fA-F]{64}")
THINK_BLOCK_PATTERN = re.compile(r"^\s*<think>(.*?)</think>", re.IGNORECASE | re.DOTALL)
THINK_STEP_PATTERN = re.compile(
    r"(?m)^\s*(?:\d+[.)、]|[一二三四五六七八九十]+[.)、）]|[-*])\s*\S+"
)
SFT_DIFFICULTY_TARGETS = {"easy": 0.25, "medium": 0.50, "hard": 0.25}
SFT_EASY_NO_THINK_TARGET = 0.70
GRPO_DIFFICULTY_TARGETS = {"hard": 0.45}
EVALUATION_TOTAL = 2_500
EVALUATION_DIFFICULTY_COUNTS = {"easy": 750, "medium": 1_250, "hard": 500}


def validate_dataset_quality(
    records: Sequence[Mapping],
    kind: str,
    *,
    expected_total: int | None = None,
    minimum_total: int | None = None,
    difficulty_targets: Mapping[str, float] | None = None,
    difficulty_tolerance: float = 0.02,
    sensitive_fields: Sequence[str] = (),
    evaluation_records: Sequence[Mapping] | None = None,
    similarity_threshold: float = 0.92,
) -> list[ValidationIssue]:
    """Apply dataset-level count, distribution, deduplication and leakage gates."""

    kind = kind.lower()
    if kind not in {"sft", "dpo", "grpo"}:
        raise ValueError(f"Unsupported dataset kind: {kind}")
    if expected_total is not None and minimum_total is not None:
        raise ValueError("Use either expected_total or minimum_total, not both")
    if not 0 <= difficulty_tolerance < 1:
        raise ValueError("difficulty_tolerance must be in [0, 1)")
    if not 0 < similarity_threshold <= 1:
        raise ValueError("similarity_threshold must be in (0, 1]")

    issues: list[ValidationIssue] = []
    total = len(records)
    if expected_total is not None and total != expected_total:
        issues.append(_dataset_issue(f"expected exactly {expected_total} records, got {total}"))
    if minimum_total is not None and total < minimum_total:
        issues.append(_dataset_issue(f"expected at least {minimum_total} records, got {total}"))

    if difficulty_targets:
        counts = Counter(str(record.get("difficulty", "")).lower() for record in records)
        missing = counts.get("", 0)
        if missing:
            issues.append(_dataset_issue(f"{missing} records are missing difficulty labels", field="difficulty"))
        if total:
            for difficulty, target in difficulty_targets.items():
                actual = counts.get(difficulty, 0) / total
                if abs(actual - target) > difficulty_tolerance:
                    issues.append(
                        _dataset_issue(
                            f"{difficulty} ratio must be {target:.2%} ± {difficulty_tolerance:.2%}, got {actual:.2%}",
                            field="difficulty",
                        )
                    )

    normalized_sensitive_fields = {
        str(field).strip(' "`[]').lower() for field in sensitive_fields if str(field).strip()
    }
    seen_fingerprints: dict[tuple[str, ...], int] = {}
    sft_easy_total = 0
    sft_easy_without_think = 0
    for line, record in enumerate(records, start=1):
        sample_id = str(record.get("id") or record.get("sample_id") or "")
        if kind == "sft":
            difficulty = str(record.get("difficulty", "")).lower()
            output = str(record.get("output", ""))
            think_match = THINK_BLOCK_PATTERN.match(output)
            think_text = think_match.group(1).strip() if think_match else ""
            has_nonempty_think = bool(think_text)
            has_think_tag = "<think>" in output.lower() or "</think>" in output.lower()
            if has_think_tag and not has_nonempty_think:
                issues.append(
                    ValidationIssue(
                        line=line,
                        sample_id=sample_id,
                        field="output",
                        message="<think> must be one non-empty leading block when present",
                    )
                )
            elif difficulty in {"medium", "hard"} and not has_nonempty_think:
                issues.append(
                    ValidationIssue(
                        line=line,
                        sample_id=sample_id,
                        field="output",
                        message=f"{difficulty} SFT samples require a non-empty <think> block",
                    )
                )
            elif difficulty in {"medium", "hard"}:
                if len(THINK_STEP_PATTERN.findall(think_text)) < 2:
                    issues.append(
                        ValidationIssue(
                            line=line,
                            sample_id=sample_id,
                            field="output",
                            message=(
                                f"{difficulty} SFT samples require at least two structured "
                                "reasoning steps in <think>"
                            ),
                        )
                    )
                if record.get("reasoning_verified") is not True:
                    issues.append(
                        ValidationIssue(
                            line=line,
                            sample_id=sample_id,
                            field="reasoning_verified",
                            message=(
                                "reasoning_verified must be true for medium/hard "
                                "structured <think> samples"
                            ),
                        )
                    )
            if difficulty == "easy":
                sft_easy_total += 1
                if not has_nonempty_think:
                    sft_easy_without_think += 1

        for verification_field in ("schema_verified", "business_definition_verified"):
            if record.get(verification_field) is not True:
                issues.append(
                    ValidationIssue(
                        line=line,
                        sample_id=sample_id,
                        field=verification_field,
                        message=f"{verification_field} must be true before final training admission",
                    )
                )

        sqls = _record_sqls(record, kind)
        for field_name, sql in sqls:
            issues.extend(
                _sensitive_sql_issues(
                    sql,
                    field_name=field_name,
                    line=line,
                    sample_id=sample_id,
                    dialect=str(record.get("dialect", "")),
                    sensitive_fields=normalized_sensitive_fields,
                )
            )

        fingerprint_fields = (
            ("query_semantic_fingerprint", "sql_ast_fingerprint", "schema_fingerprint")
            if kind == "grpo"
            else ("query_semantic_fingerprint", "sql_ast_fingerprint", "gold_result_signature")
        )
        missing_fingerprints = [
            field for field in fingerprint_fields if not str(record.get(field, "")).strip()
        ]
        if missing_fingerprints:
            issues.append(
                ValidationIssue(
                    line=line,
                    sample_id=sample_id,
                    field="fingerprints",
                    message="missing final quality fingerprints: " + ", ".join(missing_fingerprints),
                )
            )
        else:
            fingerprint = tuple(str(record[field]) for field in fingerprint_fields)
            first_line = seen_fingerprints.get(fingerprint)
            if first_line is not None:
                issues.append(
                    ValidationIssue(
                        line=line,
                        sample_id=sample_id,
                        field="fingerprints",
                        message=f"duplicate training sample fingerprint; first seen at line {first_line}",
                    )
                )
            else:
                seen_fingerprints[fingerprint] = line

        if sqls and str(record.get("sql_ast_fingerprint", "")).strip():
            try:
                actual_ast_fingerprint = fingerprint_sql_ast(
                    sqls[0][1],
                    str(record.get("dialect", "")),
                )
            except ValueError:
                actual_ast_fingerprint = ""
            if actual_ast_fingerprint and actual_ast_fingerprint != str(record["sql_ast_fingerprint"]):
                issues.append(
                    ValidationIssue(
                        line=line,
                        sample_id=sample_id,
                        field="sql_ast_fingerprint",
                        message="sql_ast_fingerprint does not match the normalized SQL AST",
                    )
                )

    if kind == "sft" and sft_easy_total:
        easy_without_think_ratio = sft_easy_without_think / sft_easy_total
        if abs(easy_without_think_ratio - SFT_EASY_NO_THINK_TARGET) > difficulty_tolerance:
            issues.append(
                _dataset_issue(
                    "easy samples without <think> must be "
                    f"{SFT_EASY_NO_THINK_TARGET:.2%} ± {difficulty_tolerance:.2%}, "
                    f"got {easy_without_think_ratio:.2%}",
                    field="output",
                )
            )

    if evaluation_records is not None:
        issues.extend(validate_evaluation_corpus(evaluation_records))
        issues.extend(
            _embedding_leakage_issues(
                records,
                evaluation_records,
                similarity_threshold=similarity_threshold,
            )
        )
    return issues


def validate_supervised_jsonl_against_sandbox(
    path: str | Path,
    kind: str,
    sandbox_db_urls: str | Mapping[str, str],
    redis_url: str,
    *,
    sensitive_fields: Sequence[str],
    query_timeout: int = 5,
    cost_threshold_rows: int = 10_000_000,
    executor_factory=None,
) -> DatasetValidationReport:
    """Execute SFT labels or both DPO choices and verify their result signatures."""

    kind = kind.lower()
    if kind not in {"sft", "dpo"}:
        raise ValueError("Sandbox-supervised validation supports sft or dpo")
    report = validate_jsonl(path, kind)
    if not report.is_valid:
        return report

    report.valid = 0
    records = read_jsonl(path)
    for line, record in enumerate(records, start=1):
        record_issues = validate_supervised_record_against_sandbox(
            record,
            kind,
            sandbox_db_urls=sandbox_db_urls,
            redis_url=redis_url,
            sensitive_fields=sensitive_fields,
            query_timeout=query_timeout,
            cost_threshold_rows=cost_threshold_rows,
            line=line,
            executor_factory=executor_factory,
        )
        report.issues.extend(record_issues)
        if not record_issues:
            report.valid += 1
    return report


def validate_supervised_record_against_sandbox(
    record: Mapping,
    kind: str,
    *,
    sandbox_db_urls: str | Mapping[str, str],
    redis_url: str,
    sensitive_fields: Sequence[str],
    query_timeout: int = 5,
    cost_threshold_rows: int = 10_000_000,
    line: int = 0,
    executor_factory=None,
) -> list[ValidationIssue]:
    """Run the final semantic correctness gate for one SFT or DPO record."""

    kind = kind.lower()
    if kind not in {"sft", "dpo"}:
        raise ValueError("Sandbox-supervised validation supports sft or dpo")
    validator = validate_sft_record if kind == "sft" else validate_dpo_record
    issues = validator(record, line=line)
    sample_id = str(record.get("id") or record.get("sample_id") or "")
    required = ("target_db", "dialect", "gold_result_signature", "reward_meta")
    for field_name in required:
        value = record.get(field_name)
        if value is None or (isinstance(value, str) and not value.strip()):
            issues.append(
                ValidationIssue(
                    line=line,
                    sample_id=sample_id,
                    field=field_name,
                    message=f"Missing sandbox quality field: {field_name}",
                )
            )
    if issues:
        return issues

    signature = str(record["gold_result_signature"]).lower()
    if not SHA256_PATTERN.fullmatch(signature):
        return [
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="gold_result_signature",
                message="gold_result_signature must be a SHA256 hex digest",
            )
        ]

    meta = record["reward_meta"]
    if not isinstance(meta, Mapping):
        return [
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="reward_meta",
                message="reward_meta must be an object",
            )
        ]
    preserve_order = meta.get("preserve_result_order")
    result_limit = meta.get("result_limit")
    max_estimated_rows = meta.get("max_estimated_rows")
    if not isinstance(preserve_order, bool):
        issues.append(_record_issue(line, sample_id, "reward_meta.preserve_result_order", "must be a boolean"))
    if isinstance(result_limit, bool) or not isinstance(result_limit, int) or not 1 <= result_limit <= 1000:
        issues.append(_record_issue(line, sample_id, "reward_meta.result_limit", "must be between 1 and 1000"))
    if isinstance(max_estimated_rows, bool) or not isinstance(max_estimated_rows, int) or max_estimated_rows <= 0:
        issues.append(_record_issue(line, sample_id, "reward_meta.max_estimated_rows", "must be positive"))
    if kind == "dpo":
        if record.get("preference_verified") is not True:
            issues.append(_record_issue(line, sample_id, "preference_verified", "must be true"))
        if not str(record.get("preference_reason", "")).strip():
            issues.append(_record_issue(line, sample_id, "preference_reason", "must explain why chosen is preferred"))
    if issues:
        return issues

    try:
        sandbox_db_url, routed_dialect = select_sandbox_route(
            sandbox_db_urls,
            str(record["target_db"]),
        )
    except ValueError as exc:
        return [_record_issue(line, sample_id, "target_db", str(exc))]
    declared_dialect = normalize_database_dialect(str(record["dialect"]))
    if declared_dialect != routed_dialect:
        return [
            _record_issue(
                line,
                sample_id,
                "dialect",
                f"declared dialect {declared_dialect!r} does not match routed dialect {routed_dialect!r}",
            )
        ]

    sensitive = {str(field).strip(' "`[]').lower() for field in sensitive_fields if str(field).strip()}
    readonly_sqls = []
    for field_name, sql in _record_sqls(record, kind):
        issues.extend(
            _sensitive_sql_issues(
                sql,
                field_name=field_name,
                line=line,
                sample_id=sample_id,
                dialect=routed_dialect,
                sensitive_fields=sensitive,
            )
        )
        if issues:
            return issues

        readonly_sql = strict_readonly_sql(sql, dialect=routed_dialect)
        if not readonly_sql:
            return [
                _record_issue(
                    line,
                    sample_id,
                    field_name,
                    "must be one valid read-only query in the routed dialect",
                )
            ]
        if preserve_order != has_top_level_order_by(readonly_sql, routed_dialect):
            return [
                _record_issue(
                    line,
                    sample_id,
                    "reward_meta.preserve_result_order",
                    f"must match whether {field_name} has a top-level ORDER BY",
                )
            ]
        readonly_sqls.append((field_name, readonly_sql))

    factory = executor_factory or build_training_executor
    executor = factory(
        sandbox_db_url=sandbox_db_url,
        redis_url=redis_url,
        query_timeout=query_timeout,
        cost_threshold_rows=cost_threshold_rows,
    )
    validation_details: dict[str, Mapping] = {}
    for field_name, readonly_sql in readonly_sqls:
        valid, error, details = executor.validate(readonly_sql, routed_dialect)
        if not valid:
            return [_record_issue(line, sample_id, field_name, f"sandbox validation failed: {error}")]
        validation_details[field_name] = details
        estimated_rows = int(details.get("estimated_rows", 0) or 0)
        if estimated_rows > max_estimated_rows:
            return [
                _record_issue(
                    line,
                    sample_id,
                    field_name,
                    f"estimated rows {estimated_rows} exceed sample limit {max_estimated_rows}",
                )
            ]
        result = executor.execute(readonly_sql, routed_dialect, limit=result_limit + 1)
        if not result.get("success"):
            return [_record_issue(line, sample_id, field_name, f"execution failed: {result.get('error', 'unknown error')}")]
        rows = result.get("data", [])
        if len(rows) > result_limit:
            return [
                _record_issue(
                    line,
                    sample_id,
                    "reward_meta.result_limit",
                    f"{field_name} returns more than result_limit={result_limit} rows",
                )
            ]
        actual_signature = result_signature(rows, preserve_order=preserve_order)
        if actual_signature != signature:
            return [
                _record_issue(
                    line,
                    sample_id,
                    field_name,
                    f"result signature mismatch: expected {signature}, got {actual_signature}",
                )
            ]

    if kind == "dpo":
        chosen_cost = validation_details["chosen"].get("estimated_cost")
        rejected_cost = validation_details["rejected"].get("estimated_cost")
        if chosen_cost is not None and rejected_cost is not None and float(chosen_cost) > float(rejected_cost):
            issues.append(
                _record_issue(
                    line,
                    sample_id,
                    "chosen/rejected",
                    f"chosen estimated cost {chosen_cost} exceeds rejected cost {rejected_cost}",
                )
            )
    return issues


def validate_grpo_split(
    train: Sequence[Mapping],
    valid: Sequence[Mapping],
    holdout: Sequence[Mapping],
    *,
    difficulty_tolerance: float = 0.02,
) -> list[ValidationIssue]:
    """Enforce the documented split, fingerprint deduplication and template isolation."""

    issues: list[ValidationIssue] = []
    sizes = (len(train), len(valid), len(holdout))
    if sizes != (8000, 1000, 1000):
        issues.append(_dataset_issue(f"GRPO split must be 8000/1000/1000, got {sizes}", field="split"))

    template_locations: dict[str, str] = {}
    seen_fingerprints: dict[tuple[str, ...], tuple[str, int]] = {}
    fingerprint_fields = SPLIT_FINGERPRINT_FIELDS[:-1]
    for split_name, records in (("train", train), ("valid", valid), ("holdout", holdout)):
        for line, record in enumerate(records, start=1):
            sample_id = str(record.get("id", ""))
            missing_fingerprints = [
                field for field in fingerprint_fields if not str(record.get(field, "")).strip()
            ]
            if missing_fingerprints:
                issues.append(
                    ValidationIssue(
                        line=line,
                        sample_id=sample_id,
                        field="fingerprints",
                        message=(
                            f"missing in {split_name} split: "
                            + ", ".join(missing_fingerprints)
                        ),
                    )
                )
            else:
                fingerprint = tuple(str(record[field]) for field in fingerprint_fields)
                first_location = seen_fingerprints.get(fingerprint)
                if first_location is not None:
                    first_split, first_line = first_location
                    issues.append(
                        ValidationIssue(
                            line=line,
                            sample_id=sample_id,
                            field="fingerprints",
                            message=(
                                "duplicate GRPO sample fingerprint; first seen in "
                                f"{first_split} line {first_line}"
                            ),
                        )
                    )
                else:
                    seen_fingerprints[fingerprint] = (split_name, line)

            template = str(record.get("business_template_id", "")).strip()
            if not template:
                issues.append(
                    ValidationIssue(
                        line=line,
                        sample_id=sample_id,
                        field="business_template_id",
                        message=f"missing in {split_name} split",
                    )
                )
                continue
            previous = template_locations.setdefault(template, split_name)
            if previous != split_name:
                issues.append(
                    ValidationIssue(
                        line=line,
                        sample_id=sample_id,
                        field="business_template_id",
                        message=f"template {template!r} crosses {previous} and {split_name}",
                    )
                )

    if train:
        hard_ratio = sum(str(record.get("difficulty", "")).lower() == "hard" for record in train) / len(train)
        if abs(hard_ratio - 0.45) > difficulty_tolerance:
            issues.append(
                _dataset_issue(
                    f"GRPO train hard ratio must be 45% ± {difficulty_tolerance:.2%}, got {hard_ratio:.2%}",
                    field="difficulty",
                )
            )
    return issues


def validate_evaluation_corpus(
    evaluation_records: Sequence[Mapping],
) -> list[ValidationIssue]:
    """Validate the fixed 2,500-row evaluation corpus used by the SFT leakage gate."""

    issues: list[ValidationIssue] = []
    if len(evaluation_records) != EVALUATION_TOTAL:
        issues.append(
            _dataset_issue(
                f"evaluation dataset must contain exactly {EVALUATION_TOTAL} records, "
                f"got {len(evaluation_records)}",
                field="evaluation_dataset",
            )
        )

    counts = Counter(str(record.get("difficulty", "")).strip().lower() for record in evaluation_records)
    invalid_difficulties = sum(
        count for difficulty, count in counts.items() if difficulty not in EVALUATION_DIFFICULTY_COUNTS
    )
    if invalid_difficulties:
        issues.append(
            _dataset_issue(
                f"evaluation dataset has {invalid_difficulties} missing or invalid difficulty labels",
                field="evaluation_dataset.difficulty",
            )
        )
    for difficulty, expected in EVALUATION_DIFFICULTY_COUNTS.items():
        actual = counts.get(difficulty, 0)
        if actual != expected:
            issues.append(
                _dataset_issue(
                    f"evaluation {difficulty} count must be {expected}, got {actual}",
                    field="evaluation_dataset.difficulty",
                )
            )

    seen_ids: dict[str, int] = {}
    for line, record in enumerate(evaluation_records, start=1):
        sample_id = str(record.get("id") or record.get("sample_id") or "").strip()
        if not sample_id:
            issues.append(
                ValidationIssue(
                    line=line,
                    field="evaluation_dataset.id",
                    message="evaluation record requires a stable id",
                )
            )
            continue
        first_line = seen_ids.get(sample_id)
        if first_line is not None:
            issues.append(
                ValidationIssue(
                    line=line,
                    sample_id=sample_id,
                    field="evaluation_dataset.id",
                    message=f"duplicate evaluation id; first seen at line {first_line}",
                )
            )
        else:
            seen_ids[sample_id] = line
    return issues


def _record_sqls(record: Mapping, kind: str) -> tuple[tuple[str, str], ...]:
    if kind == "sft":
        return (("output", str(record.get("output", ""))),)
    if kind == "dpo":
        return (
            ("chosen", str(record.get("chosen", ""))),
            ("rejected", str(record.get("rejected", ""))),
        )
    return (("gold_sql", str(record.get("gold_sql", ""))),)


def _sensitive_sql_issues(
    sql: str,
    *,
    field_name: str,
    line: int,
    sample_id: str,
    dialect: str,
    sensitive_fields: set[str],
) -> list[ValidationIssue]:
    if not sensitive_fields or not sql:
        return []
    readonly_sql = strict_readonly_sql(sql, dialect=dialect)
    if not readonly_sql:
        return []
    statement = parse_one(readonly_sql, read=sqlglot_dialect(dialect) or None)
    table_aliases = {
        table.alias_or_name.strip(' "`[]').lower(): table.name.strip(' "`[]').lower()
        for table in statement.find_all(exp.Table)
        if table.alias_or_name and table.name
    }
    selected = set()
    for column in statement.find_all(exp.Column):
        if column.is_star:
            continue
        name = column.name.strip(' "`[]').lower()
        table = column.table.strip(' "`[]').lower()
        selected.add(name)
        if table:
            selected.add(f"{table}.{name}")
            resolved_table = table_aliases.get(table)
            if resolved_table:
                selected.add(f"{resolved_table}.{name}")
    for select in statement.find_all(exp.Select):
        if any(
            isinstance(projection, exp.Star)
            or (isinstance(projection, exp.Column) and projection.is_star)
            for projection in select.expressions
        ):
            selected.add("*")
            break
    matched = sorted(sensitive_fields & selected)
    if "*" in selected:
        matched.append("*")
    if not matched:
        return []
    return [
        ValidationIssue(
            line=line,
            sample_id=sample_id,
            field=field_name,
            message="SQL selects sensitive fields: " + ", ".join(dict.fromkeys(matched)),
        )
    ]


def _embedding_leakage_issues(
    records: Sequence[Mapping],
    evaluation_records: Sequence[Mapping],
    *,
    similarity_threshold: float,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not evaluation_records:
        return [_dataset_issue("evaluation dataset must not be empty", field="query_embedding")]
    train_matrix = _embedding_matrix(records, "training", issues)
    eval_matrix = _embedding_matrix(evaluation_records, "evaluation", issues)
    if train_matrix is None or eval_matrix is None:
        return issues
    if train_matrix.shape[1] != eval_matrix.shape[1]:
        issues.append(
            _dataset_issue(
                f"training/evaluation embedding dimensions differ: {train_matrix.shape[1]} != {eval_matrix.shape[1]}",
                field="query_embedding",
            )
        )
        return issues

    eval_norms = np.linalg.norm(eval_matrix, axis=1)
    if np.any(eval_norms == 0):
        issues.append(_dataset_issue("evaluation query_embedding contains a zero vector", field="query_embedding"))
        return issues
    normalized_eval = eval_matrix / eval_norms[:, None]
    for start in range(0, len(records), 1024):
        block = train_matrix[start : start + 1024]
        norms = np.linalg.norm(block, axis=1)
        if np.any(norms == 0):
            for offset in np.flatnonzero(norms == 0):
                line = start + int(offset) + 1
                issues.append(
                    ValidationIssue(
                        line=line,
                        sample_id=str(records[line - 1].get("id", "")),
                        field="query_embedding",
                        message="query_embedding must not be a zero vector",
                    )
                )
        valid_offsets = np.flatnonzero(norms != 0)
        if not len(valid_offsets):
            continue
        similarities = (block[valid_offsets] / norms[valid_offsets, None]) @ normalized_eval.T
        max_indices = similarities.argmax(axis=1)
        max_values = similarities[np.arange(len(valid_offsets)), max_indices]
        for valid_position in np.flatnonzero(max_values > similarity_threshold):
            offset = int(valid_offsets[valid_position])
            line = start + offset + 1
            eval_index = int(max_indices[valid_position])
            issues.append(
                ValidationIssue(
                    line=line,
                    sample_id=str(records[line - 1].get("id", "")),
                    field="query_embedding",
                    message=(
                        f"evaluation leakage similarity {float(max_values[valid_position]):.6f} exceeds "
                        f"{similarity_threshold}; evaluation line {eval_index + 1}"
                    ),
                )
            )
    return issues


def _embedding_matrix(
    records: Sequence[Mapping],
    label: str,
    issues: list[ValidationIssue],
) -> np.ndarray | None:
    initial_issue_count = len(issues)
    vectors = []
    dimension = None
    for line, record in enumerate(records, start=1):
        vector = record.get("query_embedding")
        if not isinstance(vector, list) or not vector or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not np.isfinite(value)
            for value in vector
        ):
            issues.append(
                ValidationIssue(
                    line=line,
                    sample_id=str(record.get("id", "")),
                    field="query_embedding",
                    message=f"{label} query_embedding must be a non-empty finite numeric list",
                )
            )
            continue
        if dimension is None:
            dimension = len(vector)
        elif len(vector) != dimension:
            issues.append(
                ValidationIssue(
                    line=line,
                    sample_id=str(record.get("id", "")),
                    field="query_embedding",
                    message=f"{label} embedding dimension {len(vector)} does not match {dimension}",
                )
            )
            continue
        vectors.append(vector)
    if len(issues) != initial_issue_count or not vectors:
        return None
    return np.asarray(vectors, dtype=np.float64)


def _dataset_issue(message: str, field: str = "$dataset") -> ValidationIssue:
    return ValidationIssue(line=0, field=field, message=message)


def _record_issue(line: int, sample_id: str, field: str, message: str) -> ValidationIssue:
    return ValidationIssue(line=line, sample_id=sample_id, field=field, message=message)


def fingerprint_sql_ast(sql: str, dialect: str = "") -> str:
    """Return a stable SHA256 fingerprint of a normalized read-only SQL AST."""

    readonly_sql = strict_readonly_sql(sql, dialect=dialect)
    if not readonly_sql:
        raise ValueError("SQL AST fingerprint requires one valid read-only statement")
    statement = parse_one(readonly_sql, read=sqlglot_dialect(dialect) or None)
    normalized = statement.sql(dialect=sqlglot_dialect(dialect) or None, normalize=True)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
