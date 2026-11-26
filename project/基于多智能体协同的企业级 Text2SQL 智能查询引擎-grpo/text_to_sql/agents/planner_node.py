"""
Planner node: retrieval injection plus a single large-model planning call.
"""

import json
import logging
import re
from .state import Text2SQLState
from .prompts import PLANNER_PROMPT
from .fallback import FallbackPlanner
from .debug_trace import append_trace

logger = logging.getLogger(__name__)


def parse_planner_output(text: str) -> dict:
    """Parse Planner output into stable structured fields.

    JSON is accepted first for future compatibility, while the current prompt
    uses readable Chinese field labels.
    """

    result = {
        "semantic_rewrite": "",
        "business_knowledge": "",
        "execution_plan": "",
        "warnings": [],
    }
    if not text:
        return result

    parsed = _try_parse_json(text)
    if parsed:
        result.update(
            {
                "semantic_rewrite": _strip_planner_sql(
                    parsed.get("semantic_rewrite", "") or parsed.get("语义改写", "")
                ),
                "business_knowledge": _strip_planner_sql(
                    parsed.get("business_knowledge", "") or parsed.get("业务知识摘要", "")
                ),
                "execution_plan": _strip_planner_sql(
                    parsed.get("execution_plan", "") or parsed.get("执行计划", "")
                ),
                "warnings": _normalize_warnings(parsed.get("warnings", parsed.get("警告", []))),
            }
        )
        return result

    result["semantic_rewrite"] = _extract_field(text, ["语义改写", "semantic_rewrite"])
    result["business_knowledge"] = _extract_field(text, ["业务知识摘要", "business_knowledge"])
    result["execution_plan"] = _extract_execution_plan(text)
    result["warnings"] = _extract_warnings(text)
    return result


def planner_node(
    state: Text2SQLState,
    llm,
    schema_collector,
    schema_retriever,
    business_kb,
    entity_linker,
    sampling_params=None,
    table_top_k: int = 10,
    column_top_k: int = 20,
    business_kb_top_k: int = 3,
    bloodline_max_hops: int = 2,
    bloodline_max_tables: int = None,
) -> Text2SQLState:
    """Run retrieval modules, inject context, and call Planner once."""

    query = state["query"]
    debug_trace = list(state.get("debug_trace", []))

    retrieved_tables = schema_retriever.retrieve_tables(query, top_k=table_top_k)
    retrieved_columns = schema_retriever.retrieve_columns(query, tables=retrieved_tables, top_k=column_top_k)
    value_mappings = entity_linker.lookup_values(query)
    business_knowledge = business_kb.search(query, top_k=business_kb_top_k)
    debug_trace = append_trace(
        debug_trace,
        "retrieval",
        "检索输出",
        input={
            "query": query,
            "table_top_k": table_top_k,
            "column_top_k": column_top_k,
            "business_kb_top_k": business_kb_top_k,
        },
        output={
            "retrieved_tables": retrieved_tables,
            "retrieved_columns": retrieved_columns,
            "value_mappings": value_mappings,
            "business_knowledge": business_knowledge,
        },
    )

    expanded_tables = schema_collector.bloodline_completion(
        retrieved_tables,
        max_hops=bloodline_max_hops,
        max_tables=bloodline_max_tables,
    )
    compressed_schema = schema_collector.get_compressed_schema(
        tables=expanded_tables,
        target_columns=retrieved_columns,
    )
    debug_trace = append_trace(
        debug_trace,
        "schema_compression",
        "Schema 压缩输入输出",
        input={
            "retrieved_tables": retrieved_tables,
            "expanded_tables": expanded_tables,
            "target_columns": retrieved_columns,
            "bloodline_max_hops": bloodline_max_hops,
            "bloodline_max_tables": bloodline_max_tables,
        },
        output={"compressed_schema": compressed_schema},
    )

    prompt = PLANNER_PROMPT.format(
        query=query,
        business_knowledge=business_knowledge,
        compressed_schema=compressed_schema,
        value_mappings="\n".join(value_mappings) or "无",
        dialect=state.get("dialect", "mysql"),
        dialect_rules="\n".join(state.get("dialect_rules", [])) or "无",
    )

    raw_output = _invoke_planner(llm, prompt, sampling_params=sampling_params)
    planner_output = parse_planner_output(raw_output)
    if not planner_output.get("execution_plan"):
        raise ValueError("Planner output is missing a structured execution plan")
    debug_trace = append_trace(
        debug_trace,
        "agent1",
        "Agent1 输入输出",
        input={"prompt": prompt},
        output={"raw_output": raw_output, "planner_output": planner_output},
    )

    return {
        "planner_output": planner_output,
        "compressed_schema": compressed_schema,
        "business_knowledge": business_knowledge,
        "value_mappings": value_mappings,
        "candidate_tables": expanded_tables,
        "cached": False,
        "fallback": False,
        "error_msg": "",
        "debug_trace": debug_trace,
    }


def planner_node_with_fallback(
    state: Text2SQLState,
    llm,
    schema_collector,
    schema_retriever,
    business_kb,
    entity_linker,
    semantic_cache,
    sampling_params=None,
    table_top_k: int = 10,
    column_top_k: int = 20,
    business_kb_top_k: int = 3,
    bloodline_max_hops: int = 2,
    bloodline_max_tables: int = None,
    fallback_enabled: bool = True,
) -> Text2SQLState:
    """Planner wrapper with semantic-cache and heuristic fallback branches."""

    query = state["query"]

    cached = semantic_cache.get(query, schema_version=schema_collector.schema_version)
    if cached:
        debug_trace = append_trace(
            state,
            "retrieval",
            "语义缓存命中",
            input={"query": query},
            output={"cached_sql": cached},
        )
        return {
            "planner_output": {
                "semantic_rewrite": query,
                "business_knowledge": "命中语义缓存，跳过 Planner",
                "execution_plan": "命中语义缓存",
                "warnings": [],
            },
            "compressed_schema": "",
            "business_knowledge": "命中语义缓存",
            "value_mappings": [],
            "candidate_tables": [],
            "candidate_sqls": [],
            "valid_sqls": [],
            "error_history": [],
            "error_msg": "",
            "retry_count": 0,
            "final_sql": cached,
            "fallback": False,
            "cached": True,
            "debug_trace": debug_trace,
        }

    try:
        return planner_node(
            state,
            llm=llm,
            schema_collector=schema_collector,
            schema_retriever=schema_retriever,
            business_kb=business_kb,
            entity_linker=entity_linker,
            sampling_params=sampling_params,
            table_top_k=table_top_k,
            column_top_k=column_top_k,
            business_kb_top_k=business_kb_top_k,
            bloodline_max_hops=bloodline_max_hops,
            bloodline_max_tables=bloodline_max_tables,
        )
    except Exception as exc:
        if not fallback_enabled:
            raise
        logger.warning("Agent1 failed, using heuristic fallback: %s", exc)
        debug_trace = append_trace(
            state,
            "agent1",
            "Agent1 异常，进入启发式 fallback",
            input={"query": query},
            output={"error": str(exc)},
        )
        fallback = FallbackPlanner(schema_collector, entity_linker)
        fb_result = fallback.heuristic_parse(query)

        expanded_tables = schema_collector.bloodline_completion(
            fb_result.get("candidate_tables", []),
            max_hops=1,
            max_tables=bloodline_max_tables,
        )
        compressed_schema = schema_collector.get_compressed_schema(expanded_tables)
        debug_trace = append_trace(
            debug_trace,
            "schema_compression",
            "Fallback Schema 压缩输入输出",
            input={
                "candidate_tables": fb_result.get("candidate_tables", []),
                "expanded_tables": expanded_tables,
            },
            output={"compressed_schema": compressed_schema},
        )
        debug_trace = append_trace(
            debug_trace,
            "agent1",
            "Agent1 fallback 输出",
            output={"planner_output": fb_result},
        )

        return {
            "planner_output": fb_result,
            "compressed_schema": compressed_schema,
            "business_knowledge": fb_result.get("business_knowledge", ""),
            "value_mappings": fb_result.get("value_mappings", []),
            "candidate_tables": expanded_tables,
            "error_msg": f"Agent1 异常: {exc}",
            "fallback": True,
            "cached": False,
            "debug_trace": debug_trace,
        }


def _invoke_planner(llm, prompt: str, sampling_params=None) -> str:
    if sampling_params is not None and hasattr(llm, "generate"):
        outputs = llm.generate([prompt], sampling_params)
        if outputs and outputs[0].outputs:
            return outputs[0].outputs[0].text
        return ""

    if hasattr(llm, "invoke"):
        result = llm.invoke(prompt)
        return getattr(result, "content", str(result))

    if hasattr(llm, "generate"):
        outputs = llm.generate([prompt])
        if outputs and outputs[0].outputs:
            return outputs[0].outputs[0].text

    return str(llm(prompt))


def _try_parse_json(text: str) -> dict:
    text = text.strip()
    candidates = [text]
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.IGNORECASE | re.DOTALL)
    if match:
        candidates.insert(0, match.group(1).strip())
    obj_match = re.search(r"\{.*\}", text, re.DOTALL)
    if obj_match:
        candidates.append(obj_match.group(0))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(parsed, dict):
            return parsed
    return {}


def _extract_field(text: str, labels) -> str:
    label_pattern = "|".join(re.escape(label) for label in labels)
    stop_labels = "业务知识摘要|执行计划|警告|semantic_rewrite|business_knowledge|execution_plan|warnings"
    heading_prefix = r"(?:^|\n)\s*(?:#{1,6}\s*)?(?:\*\*)?\s*"
    heading_suffix = r"\s*(?:\*\*)?\s*[:：]\s*"
    pattern = (
        rf"{heading_prefix}(?:{label_pattern}){heading_suffix}"
        rf"(.*?)(?={heading_prefix}(?:{stop_labels}){heading_suffix}|\Z)"
    )
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return _strip_planner_sql(match.group(1).strip()) if match else ""


def _extract_execution_plan(text: str) -> str:
    plan = _extract_field(text, ["执行计划", "execution_plan"])
    if plan:
        return plan

    match = re.search(r"(1\.\s*.*?)(?=\n\s*警告\s*[:：]|\Z)", text, re.DOTALL)
    return _strip_planner_sql(match.group(1).strip()) if match else ""


def _strip_planner_sql(text: str) -> str:
    """Keep Agent1 output as planning context, not a hidden SQL answer."""

    if not text:
        return ""
    cleaned = re.sub(r"```sql\s*.*?```", "", text, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(
        r"\n\s*(?:#{1,6}\s*)?(?:最终\s*)?SQL\s*(?:查询|语句|query)?(?:逻辑步骤)?\s*[:：].*",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(
        r"\n\s*最终\s*SQL\s*(?:查询|语句)?\s*.*",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return cleaned.strip()


def _extract_warnings(text: str) -> list:
    field = _extract_field(text, ["警告", "warnings"])
    if not field or field.strip() == "无":
        return []
    warnings = []
    for line in field.splitlines():
        cleaned = re.sub(r"^\s*[-*\d.、]+\s*", "", line).strip()
        if cleaned and cleaned != "无":
            warnings.append(cleaned)
    return warnings or [field.strip()]


def _normalize_warnings(value) -> list:
    if not value:
        return []
    if isinstance(value, str):
        return [] if value.strip() == "无" else [value.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip() and str(item).strip() != "无"]
    return [str(value)]
