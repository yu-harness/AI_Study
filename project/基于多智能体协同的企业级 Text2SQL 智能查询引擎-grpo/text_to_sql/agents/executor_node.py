"""
Executor node: sandbox validation, execution, retry history, and best-SQL selection.
"""

import structlog
from .state import Text2SQLState
from .debug_trace import append_trace

logger = structlog.get_logger(__name__)


def executor_node(
    state: Text2SQLState,
    executor,
    selector,
    semantic_cache,
    schema_version: str = "",
) -> Text2SQLState:
    """Validate and execute SQL candidates, then update retry state."""

    candidates = state.get("candidate_sqls", [])
    error_history = list(state.get("error_history", []))
    current_errors = []
    valid_sqls = []
    debug_trace = list(state.get("debug_trace", []))

    if not candidates:
        generation_error = state.get("error_msg") or "No SQL candidates generated"
        current_errors.append(
            {
                "sql": "",
                "error": generation_error,
                "stage": "generation",
            }
        )
        logger.warning(
            "sql_generation_failed",
            sql="",
            error_msg=generation_error,
            stage="generation",
            retry_count=state.get("retry_count", 0),
            fallback=state.get("fallback", False),
        )
        debug_trace = append_trace(
            debug_trace,
            "sandbox",
            "Sandbox 未收到候选 SQL",
            output={"error": state.get("error_msg") or "No SQL candidates generated"},
            meta={"retry_count": state.get("retry_count", 0)},
        )

    for sql in candidates:
        is_valid, error, details = executor.validate(sql, state.get("dialect", "mysql"))
        candidate_checks = [
            {
                "stage": "validate",
                "success": is_valid,
                "error": error,
                "details": details,
            }
        ]
        if not is_valid:
            stage = details.get("stage", "validation") if isinstance(details, dict) else "validation"
            current_errors.append({"sql": sql, "error": error, "stage": stage})
            logger.warning(
                "sql_validation_failed",
                sql=sql,
                error_msg=error,
                stage=stage,
                retry_count=state.get("retry_count", 0),
                fallback=state.get("fallback", False),
            )
            debug_trace = append_trace(
                debug_trace,
                "sandbox",
                "Sandbox 候选检查",
                input={"sql": sql, "dialect": state.get("dialect", "mysql")},
                output={"checks": candidate_checks, "accepted": False},
                meta={"retry_count": state.get("retry_count", 0)},
            )
            continue

        exec_result = executor.execute(sql, state.get("dialect", "mysql"))
        candidate_checks.append(
            {
                "stage": "execute",
                "success": exec_result.get("success", False),
                "error": exec_result.get("error", ""),
                "row_count": exec_result.get("row_count", 0),
                "data_sample": exec_result.get("data", [])[:5],
            }
        )
        if exec_result.get("success"):
            valid_sqls.append(sql)
        else:
            current_errors.append(
                {
                    "sql": sql,
                    "error": exec_result.get("error", "execution failed"),
                    "stage": "execution",
                }
            )
            logger.warning(
                "sql_execution_failed",
                sql=sql,
                error_msg=exec_result.get("error", "execution failed"),
                stage="execution",
                retry_count=state.get("retry_count", 0),
                fallback=state.get("fallback", False),
            )
        debug_trace = append_trace(
            debug_trace,
            "sandbox",
            "Sandbox 候选检查",
            input={"sql": sql, "dialect": state.get("dialect", "mysql")},
            output={"checks": candidate_checks, "accepted": exec_result.get("success", False)},
            meta={"retry_count": state.get("retry_count", 0)},
        )

    if current_errors:
        error_history.append(
            {
                "retry": state.get("retry_count", 0),
                "errors": current_errors,
            }
        )

    if valid_sqls:
        final_sql = selector.select_best(valid_sqls, state["query"], executor, state.get("dialect", "mysql"))
        if not final_sql:
            final_sql = valid_sqls[0]
        debug_trace = append_trace(
            debug_trace,
            "selection",
            "候选 SQL 优选输出",
            input={"valid_sqls": valid_sqls, "query": state["query"]},
            output={"final_sql": final_sql},
            meta={"retry_count": state.get("retry_count", 0)},
        )
        logger.info(
            "sql_selected",
            sql=final_sql,
            retry_count=state.get("retry_count", 0),
            fallback=state.get("fallback", False),
        )
        if schema_version:
            semantic_cache.set(state["query"], final_sql, schema_version=schema_version)
        else:
            semantic_cache.set(state["query"], final_sql)
        return {
            "valid_sqls": valid_sqls,
            "final_sql": final_sql,
            "error_history": error_history,
            "error_msg": "",
            "debug_trace": debug_trace,
        }

    last_error = current_errors[-1]["error"] if current_errors else "unknown"
    next_retry = state.get("retry_count", 0) + 1
    logger.warning(
        "sql_candidates_exhausted",
        sql=current_errors[-1].get("sql", "") if current_errors else "",
        error_msg=last_error,
        retry_count=next_retry,
        fallback=state.get("fallback", False),
    )
    return {
        "valid_sqls": [],
        "final_sql": "",
        "error_history": error_history,
        "error_msg": last_error,
        "retry_count": next_retry,
        "debug_trace": debug_trace,
    }
