"""Helpers for reading timing and token fields from LangSmith runs.

Supports both persisted Run schemas and in-memory RunTree objects returned
during local evaluation. Scorer modules should use these helpers instead of
accessing run attributes directly.
"""

from datetime import datetime
from typing import Any


def run_latency_seconds(run: Any) -> float:
    """Return wall-clock duration for a run in seconds."""
    total_time = getattr(run, "total_time", None)
    if total_time is not None:
        return float(total_time)

    start = getattr(run, "start_time", None)
    end = getattr(run, "end_time", None)
    if isinstance(start, datetime) and isinstance(end, datetime):
        return max(0.0, (end - start).total_seconds())
    return 0.0


def run_total_tokens(run: Any) -> int:
    """Return total token count when present on the run or its metadata."""
    tokens = getattr(run, "total_tokens", None)
    if tokens is not None:
        return int(tokens)

    extra = getattr(run, "extra", None) or {}
    usage = extra.get("usage_metadata") or extra.get("token_usage") or {}
    if isinstance(usage, dict) and usage.get("total_tokens") is not None:
        return int(usage["total_tokens"])
    return 0


def run_child_count(run: Any) -> int:
    """Return number of child runs when available."""
    children = getattr(run, "child_runs", None) or []
    return len(children)


def trajectory_agent_tool_steps(outputs: dict[str, Any]) -> int:
    """Count agent and tools nodes in a graph trajectory attached to run outputs."""
    from harnesslab.eval.trajectory import _flatten_steps

    nodes = _flatten_steps(outputs.get("graph_trajectory", {}))
    return len([node for node in nodes if node in {"agent", "tools"}])
