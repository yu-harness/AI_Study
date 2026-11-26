"""Dataset formats and validation for the offline Text2SQL training pipeline."""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from sqlglot import ErrorLevel, TokenType, Tokenizer, exp, parse_one
from sqlglot.errors import ParseError, TokenError

from text_to_sql.agents.sql_utils import extract_readonly_sql, strip_think_block
from text_to_sql.sandbox.security import get_security_checker
from text_to_sql.training.sandbox_routes import (
    SUPPORTED_TRAINING_DIALECTS,
    build_training_executor,
    normalize_database_dialect,
    select_sandbox_route,
    sqlglot_dialect,
)


DIFFICULTIES = {"easy", "medium", "hard"}
READONLY_PREFIX = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE | re.DOTALL)
PROSE_TAIL_PATTERN = re.compile(
    r"(?:^|\n)\s*[\u4e00-\u9fff\s]*(?:解释|说明|这里|以上|返回|查询结果|最终答案)"
    r"|(?:^|\n)\s*(?:explanation|note|this query|the query|here is|returns?)\b",
    re.IGNORECASE,
)
SQL_COMMENT_PATTERN = re.compile(r"/\*.*?\*/|--[^\r\n]*", re.DOTALL)
SQL_START_PATTERN = re.compile(r"\b(?:SELECT|WITH)\b", re.IGNORECASE)
GRPO_MARKER_LINE_PATTERN = re.compile(
    r"(?m)^\s*【(?:用户问题|压缩Schema|业务知识|值映射|方言规则)】\s*$"
)
GRPO_MARKERS = (
    "【用户问题】",
    "【压缩Schema】",
    "【业务知识】",
    "【值映射】",
    "【方言规则】",
)
EMPTY_RESULT_SIGNATURE = hashlib.sha256(b"[]").hexdigest()
SPLIT_FINGERPRINT_FIELDS = (
    "query_semantic_fingerprint",
    "sql_ast_fingerprint",
    "schema_fingerprint",
    "business_template_id",
)
NONDETERMINISTIC_FUNCTION_NAMES = frozenset(
    {
        "GETDATE",
        "NEWID",
        "NOW",
        "RAND",
        "RANDOM",
        "SYS_GUID",
        "SYSDATE",
        "SYSTIMESTAMP",
        "UUID",
        "UUID_SHORT",
    }
)
NONDETERMINISTIC_EXPRESSION_TYPES = (
    exp.CurrentDate,
    exp.CurrentTime,
    exp.CurrentTimestamp,
    exp.Rand,
    exp.Uuid,
)


@dataclass
class ValidationIssue:
    """One dataset validation issue."""

    line: int
    field: str
    message: str
    sample_id: str = ""
    severity: str = "error"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DatasetValidationReport:
    """Aggregated validation result for a JSONL dataset."""

    kind: str
    path: str
    total: int = 0
    valid: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def is_valid(self) -> bool:
        return self.error_count == 0

    def add(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "path": self.path,
            "total": self.total,
            "valid": self.valid,
            "errors": self.error_count,
            "warnings": self.warning_count,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def read_jsonl(path: str | Path) -> list[dict]:
    """Read a JSONL file into dictionaries."""

    records = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if line:
                record = json.loads(line)
                if not isinstance(record, Mapping):
                    raise ValueError(f"JSONL line {line_no} must be an object")
                records.append(dict(record))
    return records


def write_jsonl(records: Iterable[Mapping], path: str | Path) -> None:
    """Write dictionaries as UTF-8 JSONL."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def to_verl_grpo_record(record: Mapping, line: int = 0) -> dict:
    """Convert one validated GRPO JSONL record to veRL's Parquet schema."""

    errors = [issue for issue in validate_grpo_record(record, line=line) if issue.severity == "error"]
    if errors:
        messages = "; ".join(f"{issue.field}: {issue.message}" for issue in errors)
        raise ValueError(f"Invalid GRPO record at line {line}: {messages}")

    return {
        "data_source": "text2sql",
        "prompt": [{"role": "user", "content": str(record["prompt"])}],
        "ability": str(record["difficulty"]),
        "reward_model": {
            "style": "rule",
            "ground_truth": str(record["gold_sql"]),
        },
        "extra_info": {
            "id": str(record["id"]),
            "difficulty": str(record["difficulty"]),
            "target_db": str(record["target_db"]),
            "dialect": str(record["dialect"]),
            "query": str(record["query"]),
            "prompt": str(record["prompt"]),
            "gold_sql": str(record["gold_sql"]),
            "gold_result_signature": str(record["gold_result_signature"]),
            "reward_meta": dict(record["reward_meta"]),
        },
    }


def write_grpo_parquet(records: Sequence[Mapping], path: str | Path) -> None:
    """Validate GRPO records and write a veRL-compatible Parquet file."""

    import pyarrow as pa
    import pyarrow.parquet as pq

    converted = [
        to_verl_grpo_record(record, line=index)
        for index, record in enumerate(records, start=1)
    ]
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(converted), target)


def assemble_sft_input(
    compressed_schema: str,
    business_knowledge: str = "无",
    value_mappings: str | Sequence[str] | None = None,
    dialect_rules: str | Sequence[str] | None = None,
    original_query: str | None = None,
    bad_sql: str | None = None,
    error_msg: str | None = None,
) -> str:
    """Build the LlamaFactory Alpaca ``input`` field used by SFT samples."""

    parts = []
    if original_query:
        parts.append(("【原始问题】", original_query))
    parts.extend(
        [
            ("【压缩Schema】", compressed_schema or "无"),
            ("【业务知识】", business_knowledge or "无"),
            ("【值映射】", _join_text(value_mappings) or "无"),
            ("【方言规则】", _join_text(dialect_rules) or "无"),
        ]
    )
    if bad_sql:
        parts.append(("【报错SQL】", bad_sql))
    if error_msg:
        parts.append(("【数据库报错】", error_msg))
    return "\n".join(f"{title}\n{body}" for title, body in parts)


def assemble_grpo_prompt(
    query: str,
    compressed_schema: str,
    business_knowledge: str = "无",
    value_mappings: str | Sequence[str] | None = None,
    dialect_rules: str | Sequence[str] | None = None,
) -> str:
    """Build the GRPO prompt, intentionally excluding Gold SQL."""

    return "\n\n".join(
        [
            f"【用户问题】\n{query}",
            f"【压缩Schema】\n{compressed_schema or '无'}",
            f"【业务知识】\n{business_knowledge or '无'}",
            f"【值映射】\n{_join_text(value_mappings) or '无'}",
            f"【方言规则】\n{_join_text(dialect_rules) or '无'}",
        ]
    )


def validate_jsonl(path: str | Path, kind: str) -> DatasetValidationReport:
    """Validate SFT, DPO, or GRPO JSONL records."""

    kind = kind.lower()
    validators = {
        "sft": validate_sft_record,
        "dpo": validate_dpo_record,
        "grpo": validate_grpo_record,
    }
    if kind not in validators:
        raise ValueError(f"Unsupported dataset kind: {kind}")

    return _validate_jsonl_records(path, kind, validators[kind])


def validate_grpo_jsonl_against_sandbox(
    path: str | Path,
    sandbox_db_urls: str | Mapping[str, str],
    redis_url: str,
    query_timeout: int = 5,
    cost_threshold_rows: int = 10_000_000,
    executor_factory: Callable[..., object] | None = None,
) -> DatasetValidationReport:
    """Validate GRPO records and execute every Gold SQL once in its routed sandbox."""

    def validator(record: Mapping, line: int = 0) -> list[ValidationIssue]:
        return validate_grpo_gold_record(
            record,
            sandbox_db_urls=sandbox_db_urls,
            redis_url=redis_url,
            query_timeout=query_timeout,
            cost_threshold_rows=cost_threshold_rows,
            line=line,
            executor_factory=executor_factory,
        )

    return _validate_jsonl_records(path, "grpo", validator)


def _validate_jsonl_records(
    path: str | Path,
    kind: str,
    validator: Callable[[Mapping, int], list[ValidationIssue]],
) -> DatasetValidationReport:
    """Apply a record validator while preserving JSONL line diagnostics."""

    report = DatasetValidationReport(kind=kind, path=str(path))
    with Path(path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            report.total += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                report.add(
                    ValidationIssue(
                        line=line_no,
                        field="$",
                        message=f"Invalid JSON: {exc}",
                    )
                )
                continue

            if not isinstance(record, Mapping):
                report.add(
                    ValidationIssue(
                        line=line_no,
                        field="$",
                        message="JSONL record must be an object",
                    )
                )
                continue

            issues = validator(record, line=line_no)
            if issues:
                for issue in issues:
                    report.add(issue)
            if not any(issue.severity == "error" for issue in issues):
                report.valid += 1
    return report


def validate_sft_record(record: Mapping, line: int = 0) -> list[ValidationIssue]:
    """Validate the LlamaFactory Alpaca SFT format from the design doc."""

    issues = _require_fields(record, ("instruction", "input", "output"), line)
    sample_id = _sample_id(record)
    output = record.get("output", "")
    readonly_sql = strict_readonly_sql(str(output)) if output else ""
    if output and not readonly_sql:
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="output",
                message="SFT output must contain exactly one read-only SQL statement with no prose tail",
            )
        )
    elif readonly_sql:
        nondeterministic = _nondeterministic_functions(readonly_sql)
        if nondeterministic:
            issues.append(
                ValidationIssue(
                    line=line,
                    sample_id=sample_id,
                    field="output",
                    message=(
                        "SFT output contains non-deterministic functions: "
                        + ", ".join(nondeterministic)
                    ),
                )
            )
    if output and not _think_tags_balanced(str(output)):
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="output",
                message="<think> tags must be balanced when present",
            )
        )
    if "history" in record and not isinstance(record.get("history"), list):
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="history",
                message="history must be a list when present",
            )
        )
    return issues


def validate_dpo_record(record: Mapping, line: int = 0) -> list[ValidationIssue]:
    """Validate a DPO preference pair for LlamaFactory."""

    issues = _require_fields(record, ("instruction", "input", "chosen", "rejected"), line)
    sample_id = _sample_id(record)
    chosen = record.get("chosen", "")
    rejected = record.get("rejected", "")
    for field_name, value in (("chosen", chosen), ("rejected", rejected)):
        readonly_sql = strict_readonly_sql(str(value)) if value else ""
        if value and not readonly_sql:
            issues.append(
                ValidationIssue(
                    line=line,
                    sample_id=sample_id,
                    field=field_name,
                    message=f"{field_name} must contain exactly one read-only SQL statement with no prose tail",
                )
            )
        elif readonly_sql:
            nondeterministic = _nondeterministic_functions(readonly_sql)
            if nondeterministic:
                issues.append(
                    ValidationIssue(
                        line=line,
                        sample_id=sample_id,
                        field=field_name,
                        message=(
                            f"{field_name} contains non-deterministic functions: "
                            + ", ".join(nondeterministic)
                        ),
                    )
                )
        if value and not _think_tags_balanced(str(value)):
            issues.append(
                ValidationIssue(
                    line=line,
                    sample_id=sample_id,
                    field=field_name,
                    message=f"{field_name} has unbalanced <think> tags",
                )
            )
    if chosen and rejected and _sql_key(chosen) == _sql_key(rejected):
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="chosen/rejected",
                message="chosen and rejected SQL should not be identical",
            )
        )
    return issues


def validate_grpo_record(record: Mapping, line: int = 0) -> list[ValidationIssue]:
    """Validate a GRPO prompt/reward sample."""

    required = (
        "id",
        "difficulty",
        "target_db",
        "dialect",
        "query",
        "prompt",
        "gold_sql",
        "gold_result_signature",
        "reward_meta",
    )
    issues = _require_fields(record, required, line)
    sample_id = _sample_id(record)

    difficulty = str(record.get("difficulty", "")).lower()
    if difficulty and difficulty not in DIFFICULTIES:
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="difficulty",
                message=f"difficulty must be one of {sorted(DIFFICULTIES)}",
            )
        )

    dialect = normalize_database_dialect(str(record.get("dialect", "")))
    if dialect and dialect not in SUPPORTED_TRAINING_DIALECTS:
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="dialect",
                message=f"dialect must be one of {sorted(SUPPORTED_TRAINING_DIALECTS)}",
            )
        )

    prompt = str(record.get("prompt", ""))
    for marker in GRPO_MARKERS:
        if marker not in prompt:
            issues.append(
                ValidationIssue(
                    line=line,
                    sample_id=sample_id,
                    field="prompt",
                    message=f"GRPO prompt is missing marker {marker}",
                )
            )

    gold_sql = str(record.get("gold_sql", ""))
    readonly_gold_sql = (
        strict_readonly_sql(gold_sql, dialect=dialect) if gold_sql else ""
    )
    if gold_sql and not readonly_gold_sql:
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="gold_sql",
                message="gold_sql must be one valid read-only query in the declared dialect",
            )
        )
    elif readonly_gold_sql:
        nondeterministic = _nondeterministic_functions(
            readonly_gold_sql,
            dialect=dialect,
        )
        if nondeterministic:
            issues.append(
                ValidationIssue(
                    line=line,
                    sample_id=sample_id,
                    field="gold_sql",
                    message=(
                        "gold_sql contains non-deterministic functions: "
                        + ", ".join(nondeterministic)
                    ),
                )
            )

    signature = str(record.get("gold_result_signature", ""))
    if signature and not re.fullmatch(r"[0-9a-fA-F]{64}", signature):
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="gold_result_signature",
                message="gold_result_signature must be a SHA256 hex digest",
            )
        )
    elif signature.lower() == EMPTY_RESULT_SIGNATURE:
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="gold_result_signature",
                message="gold_result_signature must represent a non-empty result",
            )
        )
    if gold_sql and _sql_leaks(prompt, gold_sql, dialect=dialect):
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="prompt",
                message="GRPO prompt must not expose gold_sql",
            )
        )

    meta = record.get("reward_meta", {})
    if not isinstance(meta, dict):
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="reward_meta",
                message="reward_meta must be an object",
            )
        )
        return issues

    required_tables = meta.get("required_tables")
    if not isinstance(required_tables, list) or not required_tables or any(
        not isinstance(table, str) or not table.strip() for table in required_tables
    ):
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="reward_meta.required_tables",
                message="required_tables must be a non-empty list of table names",
            )
        )
    elif readonly_gold_sql:
        referenced_tables = {
            table.name.lower()
            for table in parse_one(
                readonly_gold_sql,
                read=sqlglot_dialect(dialect) or None,
            ).find_all(exp.Table)
        }
        missing_tables = sorted(
            table
            for table in required_tables
            if table.rsplit(".", 1)[-1].strip('"`[]').lower()
            not in referenced_tables
        )
        if missing_tables:
            issues.append(
                ValidationIssue(
                    line=line,
                    sample_id=sample_id,
                    field="reward_meta.required_tables",
                    message=(
                        "required_tables are not referenced by gold_sql: "
                        + ", ".join(missing_tables)
                    ),
                )
            )
    if meta.get("non_empty_result") is not True:
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="reward_meta.non_empty_result",
                message="non_empty_result must be true",
            )
        )
    preserve_result_order = meta.get("preserve_result_order")
    if not isinstance(preserve_result_order, bool):
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="reward_meta.preserve_result_order",
                message="preserve_result_order must be a boolean",
            )
        )
    elif readonly_gold_sql:
        expected_preserve_order = has_top_level_order_by(readonly_gold_sql, dialect)
        if preserve_result_order != expected_preserve_order:
            issues.append(
                ValidationIssue(
                    line=line,
                    sample_id=sample_id,
                    field="reward_meta.preserve_result_order",
                    message=(
                        "preserve_result_order must match whether gold_sql has "
                        "a top-level ORDER BY"
                    ),
                )
            )
    max_estimated_rows = meta.get("max_estimated_rows")
    if (
        isinstance(max_estimated_rows, bool)
        or not isinstance(max_estimated_rows, int)
        or max_estimated_rows <= 0
    ):
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="reward_meta.max_estimated_rows",
                message="max_estimated_rows must be a positive integer",
            )
        )
    result_limit = meta.get("result_limit")
    if (
        isinstance(result_limit, bool)
        or not isinstance(result_limit, int)
        or not 1 <= result_limit <= 1000
    ):
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="reward_meta.result_limit",
                message="result_limit must be an integer between 1 and 1000",
            )
        )
    return issues


def validate_grpo_gold_record(
    record: Mapping,
    sandbox_db_urls: str | Mapping[str, str],
    redis_url: str,
    query_timeout: int = 5,
    cost_threshold_rows: int = 10_000_000,
    line: int = 0,
    executor_factory: Callable[..., object] | None = None,
) -> list[ValidationIssue]:
    """Validate and execute one Gold SQL record before GRPO export."""

    issues = validate_grpo_record(record, line=line)
    if any(issue.severity == "error" for issue in issues):
        return issues

    sample_id = _sample_id(record)
    try:
        sandbox_db_url, routed_dialect = select_sandbox_route(
            sandbox_db_urls,
            str(record["target_db"]),
        )
    except ValueError as exc:
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="target_db",
                message=str(exc),
            )
        )
        return issues

    declared_dialect = normalize_database_dialect(str(record["dialect"]))
    if declared_dialect != routed_dialect:
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="dialect",
                message=(
                    f"declared dialect {declared_dialect!r} does not match "
                    f"target_db route dialect {routed_dialect!r}"
                ),
            )
        )
        return issues

    factory = executor_factory or build_training_executor
    executor = factory(
        sandbox_db_url=sandbox_db_url,
        redis_url=redis_url,
        query_timeout=query_timeout,
        cost_threshold_rows=cost_threshold_rows,
    )
    gold_sql = str(record["gold_sql"])
    is_valid, error, validation_details = executor.validate(gold_sql, routed_dialect)
    if not is_valid:
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="gold_sql",
                message=f"Gold SQL sandbox validation failed: {error}",
            )
        )
        return issues

    reward_meta = record["reward_meta"]
    max_estimated_rows = reward_meta["max_estimated_rows"]
    estimated_rows = int(validation_details.get("estimated_rows", 0) or 0)
    if estimated_rows > max_estimated_rows:
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="reward_meta.max_estimated_rows",
                message=(
                    f"Gold SQL estimated rows {estimated_rows} exceed the sample limit "
                    f"{max_estimated_rows}"
                ),
            )
        )
        return issues

    result_limit = int(reward_meta["result_limit"])
    result = executor.execute(
        gold_sql,
        routed_dialect,
        limit=result_limit + 1,
    )
    if not result.get("success"):
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="gold_sql",
                message=f"Gold SQL execution failed: {result.get('error', 'unknown error')}",
            )
        )
        return issues

    rows = result.get("data", [])
    if not rows:
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="gold_result_signature",
                message="Gold SQL must return a non-empty result",
            )
        )
        return issues

    if len(rows) > result_limit:
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="reward_meta.result_limit",
                message=(
                    f"Gold SQL returns more than result_limit={result_limit} rows; "
                    "increase the limit or narrow the sample before computing its signature"
                ),
            )
        )
        return issues

    actual_signature = result_signature(
        rows,
        preserve_order=bool(reward_meta["preserve_result_order"]),
    )
    expected_signature = str(record["gold_result_signature"]).lower()
    if actual_signature != expected_signature:
        issues.append(
            ValidationIssue(
                line=line,
                sample_id=sample_id,
                field="gold_result_signature",
                message=(
                    "Gold SQL result signature mismatch: "
                    f"expected {expected_signature}, got {actual_signature}"
                ),
            )
        )
    return issues


def split_records(
    records: Sequence[Mapping],
    train_ratio: float = 0.8,
    valid_ratio: float = 0.1,
    seed: int = 2025,
    group_key: str | None = None,
    fingerprint_fields: Sequence[str] = SPLIT_FINGERPRINT_FIELDS,
) -> tuple[list[Mapping], list[Mapping], list[Mapping]]:
    """Deduplicate records and split without crossing business templates.

    The first three default fields form the GRPO sample deduplication key. The
    final field is the business-template grouping key and may not cross splits.
    ``group_key`` is an explicit legacy grouping override without deduplication.
    """

    if train_ratio <= 0 or valid_ratio <= 0 or train_ratio + valid_ratio >= 1:
        raise ValueError(
            "Expected positive train/valid/holdout ratios whose sum is 1"
        )

    if group_key:
        grouped: dict[str, list[Mapping]] = {}
        for record in records:
            value = record.get(group_key)
            if value is None or not str(value).strip():
                raise ValueError(
                    f"Record {_sample_id(record)!r} is missing split group key {group_key!r}"
                )
            grouped.setdefault(str(value), []).append(record)
        groups = list(grouped.values())
    else:
        if len(fingerprint_fields) < 2:
            raise ValueError("Expected deduplication fields followed by one template field")
        dedupe_fields = tuple(fingerprint_fields[:-1])
        template_field = fingerprint_fields[-1]
        deduplicated = _deduplicate_records(
            records,
            dedupe_fields=dedupe_fields,
            required_fields=fingerprint_fields,
        )
        grouped = {}
        for record in deduplicated:
            grouped.setdefault(str(record[template_field]), []).append(record)
        groups = list(grouped.values())

    rng = random.Random(seed)
    rng.shuffle(groups)
    groups.sort(key=len, reverse=True)

    total = sum(len(group) for group in groups)
    train_target = int(total * train_ratio)
    valid_target = int(total * valid_ratio)
    targets = (train_target, valid_target, total - train_target - valid_target)
    if len(groups) < 3 or min(targets) <= 0:
        raise ValueError(
            "An 8:1:1 group-aware split requires at least three template groups "
            "and enough deduplicated records for every split"
        )

    splits: list[list[Mapping]] = [[], [], []]
    for group_index, group in enumerate(groups):
        groups_remaining = len(groups) - group_index
        empty_splits = [index for index, split in enumerate(splits) if not split]
        candidates = (
            empty_splits
            if empty_splits and groups_remaining == len(empty_splits)
            else range(3)
        )

        def allocation_error(split_index: int) -> tuple[int, int]:
            projected = [len(split) for split in splits]
            projected[split_index] += len(group)
            absolute_error = sum(
                abs(actual - target)
                for actual, target in zip(projected, targets, strict=True)
            )
            return absolute_error, split_index

        target_split = min(candidates, key=allocation_error)
        splits[target_split].extend(group)

    train, valid, holdout = splits
    largest_group = max(map(len, groups))
    actual_sizes = tuple(map(len, splits))
    if any(not split for split in splits) or any(
        abs(actual - target) > largest_group
        for actual, target in zip(actual_sizes, targets, strict=True)
    ):
        raise ValueError(
            "Business-template groups cannot satisfy the 8:1:1 split within one "
            f"largest-group tolerance: targets={targets}, actual={actual_sizes}, "
            f"largest_group={largest_group}"
        )
    return train, valid, holdout


def _deduplicate_records(
    records: Sequence[Mapping],
    dedupe_fields: Sequence[str],
    required_fields: Sequence[str],
) -> list[Mapping]:
    """Keep the first record for each query/AST/schema composite fingerprint."""

    seen: set[tuple[str, ...]] = set()
    deduplicated = []
    for record in records:
        missing = [
            field_name
            for field_name in required_fields
            if record.get(field_name) is None or not str(record[field_name]).strip()
        ]
        if missing:
            raise ValueError(
                f"Record {_sample_id(record)!r} is missing split fingerprints: {', '.join(missing)}"
            )
        fingerprint = tuple(str(record[field_name]) for field_name in dedupe_fields)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        deduplicated.append(record)
    return deduplicated


def result_signature(rows: Iterable, preserve_order: bool = True) -> str:
    """Create a SHA256 signature for SQL result rows.

    By default row order is preserved because ORDER BY and TopN tasks are
    common in Text2SQL evaluation. Set ``preserve_order=False`` only for
    explicitly order-insensitive reward samples.
    """

    canonical_rows = []
    for row in rows:
        if hasattr(row, "_mapping"):
            row = dict(row._mapping)
        if isinstance(row, Mapping):
            canonical = {str(k): _jsonable(v) for k, v in sorted(row.items(), key=lambda item: str(item[0]))}
        else:
            canonical = [_jsonable(v) for v in row]
        canonical_rows.append(canonical)

    if not preserve_order:
        canonical_rows.sort(key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True, default=str))
    payload = json.dumps(canonical_rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def has_top_level_order_by(sql: str, dialect: str = "") -> bool:
    """Return whether the query orders its final result set."""

    statement = parse_one(sql, read=sqlglot_dialect(dialect) or None)
    return statement.args.get("order") is not None


def strict_readonly_sql(text: str, dialect: str = "") -> str:
    """Return SQL only when the model output is one pure read-only statement."""

    if not _think_tags_balanced(text):
        return ""

    after_think = strip_think_block(text).strip()
    if "```" in after_think or not READONLY_PREFIX.match(after_think):
        return ""
    if not _contains_single_statement(after_think):
        return ""
    if PROSE_TAIL_PATTERN.search(after_think):
        return ""
    if not get_security_checker().check(after_think)["safe"]:
        return ""
    sql = extract_readonly_sql(after_think)
    if not sql:
        return ""
    try:
        statement = parse_one(
            sql,
            read=sqlglot_dialect(dialect) or None,
            error_level=ErrorLevel.RAISE,
        )
    except (ParseError, ValueError):
        return ""
    if not isinstance(statement, exp.Query) or statement.find(exp.Select) is None:
        return ""
    return sql


def _require_fields(record: Mapping, fields: Sequence[str], line: int) -> list[ValidationIssue]:
    issues = []
    sample_id = _sample_id(record)
    for field_name in fields:
        value = record.get(field_name)
        if value is None or (isinstance(value, str) and not value.strip()):
            issues.append(
                ValidationIssue(
                    line=line,
                    sample_id=sample_id,
                    field=field_name,
                    message=f"Missing required field: {field_name}",
                )
            )
    return issues


def _sample_id(record: Mapping) -> str:
    return str(record.get("id") or record.get("sample_id") or "")


def _nondeterministic_functions(sql: str, dialect: str = "") -> list[str]:
    """Return non-deterministic SQL functions that make labels unreproducible."""

    statement = parse_one(sql, read=sqlglot_dialect(dialect) or None)
    found = set()
    for node in statement.walk():
        if isinstance(node, NONDETERMINISTIC_EXPRESSION_TYPES):
            found.add(node.key.upper())
            continue
        if isinstance(node, (exp.Anonymous, exp.Column)):
            name = node.name.upper()
            if name in NONDETERMINISTIC_FUNCTION_NAMES:
                found.add(name)
    return sorted(found)


def _join_text(value: str | Sequence[str] | None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return "\n".join(str(item) for item in value if str(item).strip())


def _think_tags_balanced(text: str) -> bool:
    lower = text.lower()
    opens = lower.count("<think>")
    closes = lower.count("</think>")
    if opens != closes:
        return False
    if opens == 0:
        return True
    if opens != 1:
        return False
    open_index = lower.find("<think>")
    close_index = lower.find("</think>")
    return not lower[:open_index].strip() and open_index < close_index


def _sql_key(text: str) -> str:
    sql = extract_readonly_sql(text)
    sql = sql.strip().rstrip(";")
    return " ".join(sql.lower().split())


def _sql_leaks(container: str, needle: str, dialect: str = "") -> bool:
    needle_tokens = _sql_token_key(needle)
    container_tokens = _sql_token_key(container)
    if needle_tokens and container_tokens:
        width = len(needle_tokens)
        if any(
            container_tokens[start : start + width] == needle_tokens
            for start in range(len(container_tokens) - width + 1)
        ):
            return True

    needle_key = _sql_leak_text_key(needle)
    if needle_key and needle_key in _sql_leak_text_key(container):
        return True

    needle_ast_key = _sql_ast_leak_key(needle, dialect)
    return bool(
        needle_ast_key
        and any(
            _sql_ast_leak_key(candidate, dialect) == needle_ast_key
            for candidate in _sql_leak_candidates(container)
        )
    )


def _sql_token_key(text: str) -> tuple[str, ...]:
    try:
        tokens = Tokenizer().tokenize(text)
    except TokenError:
        return ()
    return tuple(
        token.text.lower()
        for token in tokens
        if token.token_type != TokenType.SEMICOLON and token.text not in {"`", "[", "]"}
    )


def _sql_leak_text_key(text: str) -> str:
    without_comments = SQL_COMMENT_PATTERN.sub("", text)
    return re.sub(r'[\s;"`\[\]]+', "", without_comments.lower())


def _sql_leak_candidates(text: str) -> tuple[str, ...]:
    """Extract complete-looking read-only SQL fragments from GRPO prompt sections."""

    marker_starts = [match.start() for match in GRPO_MARKER_LINE_PATTERN.finditer(text)]
    candidates: list[str] = []
    seen = set()
    for match in SQL_START_PATTERN.finditer(text):
        start = match.start()
        section_end = next(
            (marker_start for marker_start in marker_starts if marker_start > start),
            len(text),
        )
        tail = text[start:section_end].strip()
        if not tail:
            continue

        variants = [tail, tail.splitlines()[0].strip(), tail.split("\n\n", 1)[0].strip()]
        semicolon = tail.find(";")
        if semicolon >= 0:
            variants.append(tail[: semicolon + 1].strip())
        for candidate in variants:
            if candidate and candidate not in seen:
                seen.add(candidate)
                candidates.append(candidate)
    return tuple(candidates)


def _sql_ast_leak_key(text: str, dialect: str) -> str:
    """Canonicalize superficial SQL rewrites that still expose the Gold answer."""

    readonly_sql = strict_readonly_sql(text, dialect=dialect)
    if not readonly_sql:
        return ""
    statement = parse_one(
        readonly_sql,
        read=sqlglot_dialect(dialect) or None,
        error_level=ErrorLevel.RAISE,
    ).copy()

    tables = list(statement.find_all(exp.Table))
    table_counts: dict[str, int] = {}
    for table in tables:
        table_name = table.name.lower()
        table_counts[table_name] = table_counts.get(table_name, 0) + 1

    table_occurrences: dict[str, int] = {}
    qualifier_map: dict[str, str] = {}
    for table in tables:
        table_name = table.name.lower()
        occurrence = table_occurrences.get(table_name, 0) + 1
        table_occurrences[table_name] = occurrence
        canonical_qualifier = (
            table_name
            if table_counts[table_name] == 1
            else f"{table_name}__{occurrence}"
        )
        qualifier_map[table_name] = canonical_qualifier
        if table.alias:
            qualifier_map[table.alias.lower()] = canonical_qualifier

    single_table = len(tables) == 1
    for column in statement.find_all(exp.Column):
        if single_table:
            column.set("table", None)
            column.set("db", None)
            column.set("catalog", None)
            continue
        qualifier = column.table.lower()
        if qualifier and qualifier in qualifier_map:
            column.set(
                "table",
                exp.Identifier(this=qualifier_map[qualifier], quoted=False),
            )
    for table in tables:
        table.set("alias", None)

    commutative_predicates = (exp.EQ, exp.NEQ, exp.NullSafeEQ, exp.NullSafeNEQ)
    for predicate in statement.find_all(*commutative_predicates):
        left = predicate.this
        right = predicate.expression
        if _sql_expression_key(left, dialect) > _sql_expression_key(right, dialect):
            predicate.set("this", right.copy())
            predicate.set("expression", left.copy())

    statement = statement.transform(
        lambda node: _sort_boolean_expression(node, dialect)
    )
    return statement.sql(
        dialect=sqlglot_dialect(dialect) or None,
        normalize=True,
        pretty=False,
    )


def _sort_boolean_expression(node: exp.Expression, dialect: str) -> exp.Expression:
    if not isinstance(node, (exp.And, exp.Or)):
        return node

    expression_type = type(node)
    terms: list[exp.Expression] = []

    def collect(expression: exp.Expression) -> None:
        if isinstance(expression, expression_type):
            collect(expression.this)
            collect(expression.expression)
        else:
            terms.append(expression)

    collect(node)
    ordered = sorted(terms, key=lambda term: _sql_expression_key(term, dialect))
    rebuilt = ordered[0].copy()
    for term in ordered[1:]:
        rebuilt = expression_type(this=rebuilt, expression=term.copy())
    return rebuilt


def _sql_expression_key(expression: exp.Expression, dialect: str) -> str:
    return expression.sql(
        dialect=sqlglot_dialect(dialect) or None,
        normalize=True,
        pretty=False,
    )


def _contains_single_statement(sql: str) -> bool:
    in_single = False
    in_double = False
    semicolon_seen = False
    i = 0
    while i < len(sql):
        ch = sql[i]
        if ch == "'" and not in_double:
            if in_single and i + 1 < len(sql) and sql[i + 1] == "'":
                i += 2
                continue
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == ";" and not in_single and not in_double:
            if semicolon_seen:
                return False
            semicolon_seen = True
            if sql[i + 1 :].strip():
                return False
        i += 1
    return True


def _jsonable(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
