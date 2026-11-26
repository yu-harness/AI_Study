"""
LangGraph workflow assembly for Text2SQL.
"""

from langgraph.graph import END, StateGraph

from .state import Text2SQLState


_router_wrapper = None
_planner_wrapper = None
_coder_wrapper = None
_executor_wrapper = None


def init_workflow(router_fn, planner_fn, coder_fn, executor_fn):
    """Inject node functions used by create_workflow."""

    global _router_wrapper, _planner_wrapper, _coder_wrapper, _executor_wrapper
    _router_wrapper = router_fn
    _planner_wrapper = planner_fn
    _coder_wrapper = coder_fn
    _executor_wrapper = executor_fn


def create_workflow(max_retries: int = 3):
    """Create the Text2SQL workflow graph.

    max_retries is the number of repair rounds allowed after the initial
    candidate batch fails.
    """

    _ensure_initialized()

    workflow = StateGraph(Text2SQLState)
    workflow.add_node("Router", _router_wrapper)
    workflow.add_node("Planner", _planner_wrapper)
    workflow.add_node("Coder", _coder_wrapper)
    workflow.add_node("Executor", _executor_wrapper)

    workflow.set_entry_point("Router")
    workflow.add_edge("Router", "Planner")

    workflow.add_conditional_edges(
        "Planner",
        _route_after_planner,
        {
            "success_end": END,
            "continue": "Coder",
        },
    )
    workflow.add_edge("Coder", "Executor")
    workflow.add_conditional_edges(
        "Executor",
        lambda state: _route_after_executor(state, max_retries=max_retries),
        {
            "success_end": END,
            "fail_end": END,
            "retry": "Coder",
        },
    )

    return workflow.compile()


def _route_after_planner(state: Text2SQLState) -> str:
    if state.get("final_sql"):
        return "success_end"
    return "continue"


def _route_after_executor(state: Text2SQLState, max_retries: int) -> str:
    if state.get("final_sql"):
        return "success_end"
    if state.get("retry_count", 0) > max_retries:
        return "fail_end"
    return "retry"


def _ensure_initialized():
    missing = [
        name
        for name, fn in {
            "router_fn": _router_wrapper,
            "planner_fn": _planner_wrapper,
            "coder_fn": _coder_wrapper,
            "executor_fn": _executor_wrapper,
        }.items()
        if fn is None
    ]
    if missing:
        raise RuntimeError(f"Workflow nodes are not initialized: {', '.join(missing)}")
