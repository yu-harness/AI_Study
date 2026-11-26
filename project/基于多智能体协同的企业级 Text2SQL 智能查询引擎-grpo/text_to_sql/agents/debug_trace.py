"""Helpers for building JSON-safe workflow debug traces."""

from collections.abc import Mapping


def append_trace(trace_or_state, stage: str, title: str, input=None, output=None, meta=None) -> list:
    """Return a new trace list with one JSON-safe event appended."""

    if isinstance(trace_or_state, dict):
        trace = list(trace_or_state.get("debug_trace", []))
    else:
        trace = list(trace_or_state or [])

    event = {
        "stage": stage,
        "title": title,
    }
    if input is not None:
        event["input"] = to_json_safe(input)
    if output is not None:
        event["output"] = to_json_safe(output)
    if meta is not None:
        event["meta"] = to_json_safe(meta)
    trace.append(event)
    return trace


def to_json_safe(value, depth: int = 0):
    """Convert common runtime objects to JSON-safe primitives."""

    if depth > 6:
        return str(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {str(key): to_json_safe(item, depth + 1) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_json_safe(item, depth + 1) for item in value]
    if hasattr(value, "_mapping"):
        return to_json_safe(dict(value._mapping), depth + 1)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
