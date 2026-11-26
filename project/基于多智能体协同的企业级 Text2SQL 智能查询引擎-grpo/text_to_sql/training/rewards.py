"""Reward functions for Text2SQL GRPO training."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from typing import Callable, Mapping
from urllib.parse import urlparse

from text_to_sql.llm.ollama_client import OllamaLLM, OllamaSamplingParams
from text_to_sql.training.data import (
    EMPTY_RESULT_SIGNATURE,
    has_top_level_order_by as _has_top_level_order_by,
    result_signature,
    strict_readonly_sql,
)
from text_to_sql.training.sandbox_routes import (
    build_training_executor as _build_executor,
    normalize_database_dialect as _normalize_database_dialect,
    select_sandbox_route as _select_sandbox_route,
)


THINK_BLOCK = re.compile(r"^\s*<think>(.*?)</think>\s*", re.IGNORECASE | re.DOTALL)


@dataclass
class RewardResult:
    """Structured reward output consumed by GRPO trainers and tests."""

    total: float
    format_reward: float
    execution_reward: float
    judge_reward: float
    penalty: float
    sql: str = ""
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_metrics(self) -> dict[str, float]:
        """Return numeric metrics accepted by veRL's reward adapter."""

        return {
            "score": self.total,
            "format_reward": self.format_reward,
            "execution_reward": self.execution_reward,
            "execution_correct": self.execution_reward,
            "judge_reward": self.judge_reward,
            "penalty": self.penalty,
        }


def format_verification_reward(
    model_output: str,
    min_response_tokens: int = 50,
    token_counter: Callable[[str], int] | None = None,
    require_think: bool = True,
) -> float:
    """Reward one non-empty ``<think>...</think>SQL`` response."""

    if not model_output or not strict_readonly_sql(model_output):
        return 0.0
    if require_think:
        think = THINK_BLOCK.match(model_output)
        if think is None or not think.group(1).strip():
            return 0.0

    count_tokens = token_counter or _token_count
    if count_tokens(model_output) < min_response_tokens:
        return 0.5
    return 1.0


def qwen35_judge_reward(
    query: str,
    candidate_sql: str,
    gold_sql: str,
    prompt_context: str,
    required_tables: list[str],
    base_url: str,
    model: str = "qwen3.5:4b",
    timeout: int = 240,
) -> float:
    """Use a loopback-only Qwen3.5 Judge for semantic SQL scoring."""

    _require_loopback_url(base_url)
    judge_input = {
        "query": query,
        "candidate_sql": candidate_sql,
        "gold_sql": gold_sql,
        "required_tables": required_tables,
        "prompt_context": prompt_context,
    }
    prompt = (
        "你是严格的 Text2SQL 语义裁判。根据用户问题、Schema/业务上下文和 Gold SQL，"
        "判断 candidate_sql 是否语义正确。Gold SQL 只是参考，允许语义等价写法。"
        "完全正确为 1，完全错误为 0，部分正确取 0 到 1 之间。只返回符合指定结构的 JSON。\n\n"
        + json.dumps(judge_input, ensure_ascii=False, sort_keys=True)
    )
    schema = {
        "type": "object",
        "properties": {
            "score": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
            }
        },
        "required": ["score"],
    }
    judge = _build_local_judge(base_url, model, int(timeout))
    output = judge.generate(
        [prompt],
        OllamaSamplingParams(
            temperature=0.0,
            top_p=1.0,
            max_tokens=64,
            think=False,
            format=schema,
        ),
    )[0].outputs[0].text
    verdict = json.loads(output)
    return _normalize_judge_score(verdict["score"])


def _normalize_judge_score(score: float | None) -> float:
    """Normalize a judge score into the 0..1 reward range."""

    if score is None:
        return 0.0
    return max(0.0, min(1.0, float(score)))


def sandbox_execution_reward(
    sql: str,
    executor,
    dialect: str = "mysql",
    gold_sql: str = "",
    gold_result_signature: str = "",
    require_non_empty: bool = False,
    result_limit: int = 1000,
    max_estimated_rows: int = 10_000_000,
    preserve_result_order: bool | None = None,
) -> tuple[float, float, dict]:
    """Run SQL through the sandbox and return ``(exec_reward, penalty, details)``."""

    expected_signature = str(gold_result_signature).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected_signature):
        raise ValueError("gold_result_signature must be a SHA256 hex digest")
    if expected_signature == EMPTY_RESULT_SIGNATURE:
        raise ValueError("gold_result_signature must represent a non-empty result")

    details = {
        "dialect": dialect,
        "result_limit": result_limit,
        "max_estimated_rows": max_estimated_rows,
    }
    if not sql:
        details["error"] = "empty SQL"
        return 0.0, 1.0, details

    is_valid, error, validation = executor.validate(sql, dialect=dialect)
    details["validation"] = validation
    if not is_valid:
        details["error"] = error
        penalty = 0.5 if validation.get("stage") == "cost" else 0.0
        if penalty:
            details["cost_penalty"] = True
        return 0.0, penalty, details

    estimated_rows = int(validation.get("estimated_rows", 0) or 0)
    penalty = 0.5 if estimated_rows > max_estimated_rows else 0.0
    if penalty:
        details["cost_penalty"] = True
        return 0.0, penalty, details

    if preserve_result_order is None:
        preserve_result_order = _has_top_level_order_by(gold_sql or sql, dialect)
    details["preserve_result_order"] = preserve_result_order

    result = executor.execute(sql, dialect=dialect, limit=result_limit + 1)
    details["execution"] = result
    if not result.get("success"):
        return 0.0, penalty, details

    rows = result.get("data", [])
    if len(rows) > result_limit:
        penalty += 0.5
        details["result_limit_exceeded"] = True
        return 0.0, penalty, details

    signature = result_signature(rows, preserve_order=preserve_result_order)
    details["result_signature"] = signature
    if require_non_empty and not rows:
        penalty += 0.5
        details["empty_result_penalty"] = True

    details["expected_signature"] = expected_signature
    details["expected_signature_source"] = "gold_result_signature"
    return (1.0 if signature == expected_signature else 0.0), penalty, details


def compute_grpo_reward(
    model_output: str,
    sample: Mapping,
    executor=None,
    judge_score: float | None = None,
    token_counter: Callable[[str], int] | None = None,
) -> RewardResult:
    """Compute ``R_total = R_format * (R_exec + 0.2 * R_judge - R_penalty)``."""

    if executor is None:
        raise ValueError("GRPO reward requires a configured sandbox executor")

    sql = strict_readonly_sql(model_output)
    format_reward = format_verification_reward(model_output, token_counter=token_counter)
    judge_reward = _normalize_judge_score(judge_score)
    details = {"sample_id": sample.get("id", "")}

    dialect = str(sample.get("dialect", "")).strip()
    if not dialect:
        raise ValueError("GRPO reward sample requires dialect")
    meta = sample.get("reward_meta")
    if not isinstance(meta, Mapping):
        raise ValueError("GRPO reward sample requires reward_meta")
    if meta.get("non_empty_result") is not True:
        raise ValueError("reward_meta.non_empty_result must be true")
    preserve_result_order = meta.get("preserve_result_order")
    if not isinstance(preserve_result_order, bool):
        raise ValueError("reward_meta.preserve_result_order must be a boolean")
    gold_sql = str(sample.get("gold_sql", "")).strip()
    if not gold_sql:
        raise ValueError("GRPO reward sample requires gold_sql")
    if preserve_result_order != _has_top_level_order_by(gold_sql, dialect):
        raise ValueError(
            "reward_meta.preserve_result_order must match whether gold_sql has "
            "a top-level ORDER BY"
        )
    required_tables = meta.get("required_tables")
    if not isinstance(required_tables, list) or not required_tables or any(
        not isinstance(table, str) or not table.strip() for table in required_tables
    ):
        raise ValueError("reward_meta.required_tables must be a non-empty list")
    result_limit = meta.get("result_limit")
    if (
        isinstance(result_limit, bool)
        or not isinstance(result_limit, int)
        or not 1 <= result_limit <= 1000
    ):
        raise ValueError("reward_meta.result_limit must be between 1 and 1000")
    max_estimated_rows = meta.get("max_estimated_rows")
    if (
        isinstance(max_estimated_rows, bool)
        or not isinstance(max_estimated_rows, int)
        or max_estimated_rows <= 0
    ):
        raise ValueError("reward_meta.max_estimated_rows must be a positive integer")

    execution_reward, penalty, execution_details = sandbox_execution_reward(
        sql=sql,
        executor=executor,
        dialect=dialect,
        gold_sql=gold_sql,
        gold_result_signature=sample.get("gold_result_signature", ""),
        require_non_empty=True,
        result_limit=result_limit,
        max_estimated_rows=max_estimated_rows,
        preserve_result_order=preserve_result_order,
    )
    details.update(execution_details)

    total = format_reward * (execution_reward + 0.2 * judge_reward - penalty)
    return RewardResult(
        total=total,
        format_reward=format_reward,
        execution_reward=execution_reward,
        judge_reward=judge_reward,
        penalty=penalty,
        sql=sql,
        details=details,
    )


async def compute_score(
    data_source: str,
    solution_str: str,
    ground_truth: str,
    extra_info: Mapping | None = None,
    *,
    sandbox_db_urls: str | Mapping[str, str],
    redis_url: str,
    judge_base_url: str,
    tokenizer_path: str,
    judge_model: str = "qwen3.5:4b",
    judge_timeout: int = 240,
    query_timeout: int = 5,
    cost_threshold_rows: int = 10_000_000,
) -> dict[str, float]:
    """Asynchronous veRL adapter backed by sandbox execution and local Qwen."""

    return await asyncio.to_thread(
        _compute_score_sync,
        data_source,
        solution_str,
        ground_truth,
        extra_info,
        sandbox_db_urls=sandbox_db_urls,
        redis_url=redis_url,
        judge_base_url=judge_base_url,
        tokenizer_path=tokenizer_path,
        judge_model=judge_model,
        judge_timeout=judge_timeout,
        query_timeout=query_timeout,
        cost_threshold_rows=cost_threshold_rows,
    )


def _compute_score_sync(
    data_source: str,
    solution_str: str,
    ground_truth: str,
    extra_info: Mapping | None,
    *,
    sandbox_db_urls: str | Mapping[str, str],
    redis_url: str,
    judge_base_url: str,
    tokenizer_path: str,
    judge_model: str,
    judge_timeout: int,
    query_timeout: int,
    cost_threshold_rows: int,
) -> dict[str, float]:
    """Compute one reward and its group-filter/observability metrics."""

    if data_source != "text2sql":
        raise ValueError(f"Unsupported reward data source: {data_source}")
    if not isinstance(extra_info, Mapping):
        raise ValueError("Text2SQL reward requires the GRPO extra_info mapping")

    sample = dict(extra_info)
    recorded_gold = str(sample.get("gold_sql", ""))
    if recorded_gold and ground_truth and recorded_gold != str(ground_truth):
        raise ValueError("ground_truth does not match extra_info.gold_sql")
    sample["gold_sql"] = recorded_gold or str(ground_truth)
    target_db = str(sample.get("target_db", ""))
    sandbox_db_url, routed_dialect = _select_sandbox_route(sandbox_db_urls, target_db)
    declared_dialect = _normalize_database_dialect(str(sample.get("dialect", "")))
    if declared_dialect != routed_dialect:
        raise ValueError(
            "GRPO sample dialect does not match target_db route: "
            f"declared={declared_dialect or '<missing>'}, routed={routed_dialect}"
        )
    sample["dialect"] = routed_dialect

    executor = _build_executor(
        sandbox_db_url=sandbox_db_url,
        redis_url=redis_url,
        query_timeout=int(query_timeout),
        cost_threshold_rows=int(cost_threshold_rows),
    )
    token_counter = lambda text: _token_count(text, tokenizer_path=tokenizer_path)
    preliminary = compute_grpo_reward(
        model_output=solution_str,
        sample=sample,
        executor=executor,
        judge_score=0.0,
        token_counter=token_counter,
    )
    if preliminary.format_reward == 0.0:
        return preliminary.to_metrics()

    meta = sample.get("reward_meta", {}) or {}
    judge_reward = qwen35_judge_reward(
        query=str(sample.get("query", "")),
        candidate_sql=preliminary.sql,
        gold_sql=str(sample.get("gold_sql", "")),
        prompt_context=str(sample.get("prompt", "")),
        required_tables=list(meta.get("required_tables", [])),
        base_url=judge_base_url,
        model=judge_model,
        timeout=int(judge_timeout),
    )
    preliminary.judge_reward = judge_reward
    preliminary.total = preliminary.format_reward * (
        preliminary.execution_reward + 0.2 * judge_reward - preliminary.penalty
    )
    return preliminary.to_metrics()


@lru_cache(maxsize=8)
def _build_local_judge(base_url: str, model: str, timeout: int) -> OllamaLLM:
    _require_loopback_url(base_url)
    return OllamaLLM(
        model=model,
        base_url=base_url,
        timeout=timeout,
        keep_alive="10m",
        max_parallel=1,
    )


def _require_loopback_url(base_url: str) -> None:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
        "127.0.0.1",
        "localhost",
        "::1",
    }:
        raise ValueError("Training Judge must use a loopback-only Ollama URL")


@lru_cache(maxsize=4)
def _load_tokenizer(tokenizer_path: str):
    if not tokenizer_path:
        raise ValueError("tokenizer_path is required for the GRPO length penalty")
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)


def _token_count(text: str, tokenizer_path: str = "") -> int:
    if tokenizer_path:
        tokenizer = _load_tokenizer(tokenizer_path)
        return len(tokenizer.encode(text or "", add_special_tokens=False))
    return len(re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+|[^\s]", text or ""))
