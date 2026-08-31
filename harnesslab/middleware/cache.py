"""In-run memoization for idempotent read tools."""

import json
from typing import Any

CACHEABLE_TOOLS = frozenset(
    {
        "read_incident",
        "read_topic",
        "fetch_metrics",
        "read_source",
        "search_literature",
        "search_runbooks",
        "correlate_timeline",
    }
)


def cache_key(tool_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    """Build a stable cache key from tool name and arguments."""
    payload = {"args": args, "kwargs": kwargs}
    return f"{tool_name}:{json.dumps(payload, sort_keys=True, default=str)}"


def get_cached_result(tool_name: str, key: str, context: dict) -> Any | None:
    """Return a cached tool result when present."""
    if tool_name not in CACHEABLE_TOOLS:
        return None
    return context["tool_cache"].get(key)


def store_cached_result(tool_name: str, key: str, result: Any, context: dict) -> None:
    """Store a successful read tool result for this run."""
    if tool_name not in CACHEABLE_TOOLS:
        return
    context["tool_cache"][key] = result
