"""
Coder node for SQL generation and retry repair.
"""

import logging
import re
from .state import Text2SQLState
from .prompts import CODER_PROMPT, REPAIR_PROMPT, build_error_history_text, format_execution_plan
from .sql_utils import normalize_sql_candidates
from .debug_trace import append_trace

logger = logging.getLogger(__name__)


def coder_node(state: Text2SQLState, coder_agent, max_candidates: int = 3) -> Text2SQLState:
    """Generate SQL candidates on first pass, then repair from error history."""

    if state.get("final_sql"):
        return {"candidate_sqls": []}

    if state.get("retry_count", 0) > 0:
        return _retry_coder(state, coder_agent)
    return _first_coder(state, coder_agent, max_candidates)


def _first_coder(state: Text2SQLState, coder_agent, max_candidates: int = 3) -> Text2SQLState:
    """Generate multiple SQL candidates for the first attempt."""

    prompt = CODER_PROMPT.format(
        query=state["query"],
        plan=format_execution_plan(state.get("planner_output", {})),
        schema=state.get("compressed_schema") or "无可用表结构",
        business_knowledge=state.get("business_knowledge") or "无",
        dialect=state.get("dialect", "mysql"),
        dialect_rules="\n".join(state.get("dialect_rules", [])) or "无",
        value_mappings="\n".join(state.get("value_mappings", [])) or "无",
    )

    raw_sqls = coder_agent.generate_with_retry(prompt, n=max_candidates)
    sqls = normalize_sql_candidates(raw_sqls)
    sqls, intent_errors = filter_sqls_by_query_intent(sqls, state["query"])
    logger.info("Generated %s read-only SQL candidates", len(sqls))
    error_msg = _candidate_error_message(sqls, intent_errors, "Coder returned no read-only SQL")
    debug_trace = append_trace(
        state,
        "agent2",
        "Agent2 首轮输入输出",
        input={"prompt": prompt, "max_candidates": max_candidates},
        output={
            "raw_outputs": raw_sqls,
            "candidate_sqls": sqls,
            "intent_errors": intent_errors,
            "error_msg": error_msg,
        },
        meta={"retry_count": state.get("retry_count", 0)},
    )
    return {"candidate_sqls": sqls, "error_msg": error_msg, "debug_trace": debug_trace}


def _retry_coder(state: Text2SQLState, coder_agent) -> Text2SQLState:
    """Repair SQL using cumulative executor error history."""

    prompt = REPAIR_PROMPT.format(
        query=state["query"],
        dialect=state.get("dialect", "mysql"),
        dialect_rules="\n".join(state.get("dialect_rules", [])) or "无",
        schema=state.get("compressed_schema") or "无可用表结构",
        plan=format_execution_plan(state.get("planner_output", {})),
        value_mappings="\n".join(state.get("value_mappings", [])) or "无",
        error_history_text=build_error_history_text(state.get("error_history", [])),
    )

    raw_sql = coder_agent.single_repair(prompt)
    sqls = normalize_sql_candidates([raw_sql])
    sqls, intent_errors = filter_sqls_by_query_intent(sqls, state["query"])
    error_msg = _candidate_error_message(sqls, intent_errors, "Coder repair returned no read-only SQL")
    debug_trace = append_trace(
        state,
        "reflection",
        "反思修复输入输出",
        input={
            "prompt": prompt,
            "error_history": state.get("error_history", []),
        },
        output={
            "raw_output": raw_sql,
            "candidate_sqls": sqls,
            "intent_errors": intent_errors,
            "error_msg": "" if sqls else error_msg,
        },
        meta={"retry_count": state.get("retry_count", 0)},
    )
    if sqls:
        logger.info("Retry generated SQL: %s...", sqls[0][:100])
        return {"candidate_sqls": sqls, "error_msg": "", "debug_trace": debug_trace}

    logger.warning("Retry did not produce read-only SQL")
    return {
        "candidate_sqls": [],
        "error_msg": error_msg,
        "debug_trace": debug_trace,
    }


AGGREGATE_SQL_PATTERN = re.compile(r"\b(SUM|AVG|COUNT|MIN|MAX)\s*\(|\bGROUP\s+BY\b", re.IGNORECASE)
AGGREGATE_QUERY_TERMS = (
    "统计",
    "总和",
    "合计",
    "汇总",
    "累计",
    "平均",
    "均值",
    "数量",
    "个数",
    "多少",
    "最大",
    "最小",
    "最高",
    "最低",
    "排名",
    "排行",
    "占比",
    "比例",
    "率",
    "sum",
    "total",
    "count",
    "average",
    "avg",
    "max",
    "min",
    "rank",
)
STATUS_QUERY_TERMS = {
    "paid": ("已支付", "支付", "付款", "paid"),
    "refunded": ("已退款", "退款", "refunded"),
    "cancelled": ("已取消", "取消", "cancelled", "canceled"),
}
STATUS_FILTER_PATTERN = re.compile(
    r"\bstatus\b\s*(?:=|IN)\s*\(?\s*['\"]?(paid|refunded|cancelled|canceled)['\"]?",
    re.IGNORECASE,
)
ACTIVE_QUERY_TERMS = ("活跃", "启用", "激活", "有效", "active", "enabled")
POSITIVE_AMOUNT_QUERY_TERMS = (
    "正金额",
    "非负",
    "大于0",
    "大于 0",
    "大于零",
    "正数",
    "positive",
    "non-negative",
    "nonnegative",
)
TIME_QUERY_TERMS = (
    "时间",
    "日期",
    "最近",
    "近",
    "今天",
    "昨天",
    "本周",
    "本月",
    "今年",
    "去年",
    "之前",
    "之后",
    "date",
    "time",
    "day",
    "week",
    "month",
    "year",
    "before",
    "after",
    "between",
)
ACTIVE_FILTER_PATTERN = re.compile(
    r"\b(?:active|is_active|enabled|is_enabled)\b\s*=\s*(?:1|true)",
    re.IGNORECASE,
)
POSITIVE_AMOUNT_FILTER_PATTERN = re.compile(
    r"\b(?:amount|price|revenue|gmv)\b\s*(?:>=|>)\s*0\b",
    re.IGNORECASE,
)
TIME_FILTER_PATTERN = re.compile(
    r"\b(?:created_at|updated_at|created_time|updated_time|date|dt|time)\b\s*(?:>=|<=|>|<|\bBETWEEN\b)",
    re.IGNORECASE,
)


def filter_sqls_by_query_intent(sqls: list, query: str) -> tuple:
    """Reject SQL candidates that add intent-changing logic not present in query."""

    accepted = []
    errors = []
    for sql in sqls:
        reason = validate_sql_matches_query_intent(sql, query)
        if reason:
            errors.append({"sql": sql, "error": reason, "stage": "intent"})
        else:
            accepted.append(sql)
    return accepted, errors


def validate_sql_matches_query_intent(sql: str, query: str) -> str:
    """Return an error message when SQL drifts from explicit user intent."""

    query_text = (query or "").lower()
    if AGGREGATE_SQL_PATTERN.search(sql or "") and not _contains_any(query_text, AGGREGATE_QUERY_TERMS):
        return (
            "Query asks for detail fields, but SQL uses aggregation. "
            "Use aggregate functions only when the user explicitly asks for statistics, totals, counts, averages, or rankings."
        )

    for status in STATUS_FILTER_PATTERN.findall(sql or ""):
        normalized = "cancelled" if status.lower() == "canceled" else status.lower()
        if not _contains_any(query_text, STATUS_QUERY_TERMS.get(normalized, ())):
            return (
                f"SQL adds status='{normalized}' filter, but the user did not request that status. "
                "Do not add business filters unless they are explicit in the question or value mappings."
            )
    if ACTIVE_FILTER_PATTERN.search(sql or "") and not _contains_any(query_text, ACTIVE_QUERY_TERMS):
        return (
            "SQL adds active/enabled filter, but the user did not request active records. "
            "Do not add business filters unless they are explicit in the question or value mappings."
        )
    if POSITIVE_AMOUNT_FILTER_PATTERN.search(sql or "") and not _contains_any(query_text, POSITIVE_AMOUNT_QUERY_TERMS):
        return (
            "SQL adds amount > 0 or amount >= 0 filter, but the user did not request a positive amount constraint. "
            "Do not add business filters unless they are explicit in the question or value mappings."
        )
    if TIME_FILTER_PATTERN.search(sql or "") and not _contains_any(query_text, TIME_QUERY_TERMS):
        return (
            "SQL adds a time range filter, but the user did not request a time range. "
            "Do not add business filters unless they are explicit in the question or value mappings."
        )
    return ""


def _contains_any(text: str, terms) -> bool:
    return any(term.lower() in text for term in terms)


def _candidate_error_message(sqls: list, intent_errors: list, fallback: str) -> str:
    if sqls:
        return ""
    if intent_errors:
        return "; ".join(error["error"] for error in intent_errors)
    return fallback
