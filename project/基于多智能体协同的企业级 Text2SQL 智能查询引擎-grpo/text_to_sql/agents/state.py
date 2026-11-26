"""
Agent state definitions for the LangGraph Text2SQL workflow.
"""

from typing import Dict, List, TypedDict
from uuid import uuid4


class Text2SQLState(TypedDict):
    """Shared state passed between Router, Planner, Coder, and Executor."""

    # Input
    query: str

    # Router output
    target_db: str
    dialect: str
    dialect_rules: List[str]

    # Planner output
    planner_output: Dict
    compressed_schema: str
    business_knowledge: str
    value_mappings: List[str]
    candidate_tables: List[str]

    # Coder output
    candidate_sqls: List[str]
    valid_sqls: List[str]
    error_history: List[Dict]
    error_msg: str

    # Execution state
    retry_count: int
    final_sql: str

    # Metadata
    fallback: bool
    cached: bool
    trace_id: str
    debug_trace: List[Dict]


def build_initial_state(
    query: str,
    target_db: str = "",
    dialect: str = "mysql",
    dialect_rules: List[str] = None,
    trace_id: str = None,
) -> Text2SQLState:
    """Build a complete initial workflow state with stable defaults."""

    return Text2SQLState(
        query=query,
        target_db=target_db,
        dialect=dialect,
        dialect_rules=list(dialect_rules or []),
        planner_output={},
        compressed_schema="",
        business_knowledge="",
        value_mappings=[],
        candidate_tables=[],
        candidate_sqls=[],
        valid_sqls=[],
        error_history=[],
        error_msg="",
        retry_count=0,
        final_sql="",
        fallback=False,
        cached=False,
        trace_id=trace_id or uuid4().hex,
        debug_trace=[],
    )
