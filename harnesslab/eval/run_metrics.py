"""Helpers for reading timing and token fields from LangSmith runs.

Supports both persisted Run schemas and in-memory RunTree objects returned
during local evaluation. Scorer modules should use these helpers instead of
accessing run attributes directly.
"""

from datetime import datetime
from typing import Any

from harnesslab.eval.outputs import run_output_field
from harnesslab.eval.token_usage import aggregate_usage_metadata, usage_dict_total_tokens


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

    outputs = getattr(run, "outputs", None) or {}
    if isinstance(outputs, dict):
        output_tokens = outputs.get("total_tokens")
        if output_tokens is not None:
            return int(output_tokens)

        usage = outputs.get("usage_metadata")
        if isinstance(usage, dict):
            if usage and all(isinstance(value, dict) for value in usage.values()):
                total, _ = aggregate_usage_metadata(usage)
                if total > 0:
                    return total
            token_total = usage_dict_total_tokens(usage)
            if token_total > 0:
                return token_total

    extra = getattr(run, "extra", None) or {}
    usage = extra.get("usage_metadata") or extra.get("token_usage") or {}
    if isinstance(usage, dict):
        if usage.get("total_tokens") is not None:
            return int(usage["total_tokens"])
        if usage and all(isinstance(value, dict) for value in usage.values()):
            total, _ = aggregate_usage_metadata(usage)
            if total > 0:
                return total

    children = getattr(run, "child_runs", None) or []
    child_total = sum(run_total_tokens(child) for child in children)
    if child_total > 0:
        return child_total

    return 0


def run_child_count(run: Any) -> int:
    """Return number of child runs when available."""
    children = getattr(run, "child_runs", None) or []
    return len(children)


def trajectory_agent_tool_steps(outputs: dict[str, Any]) -> int:
    """Count agent and tools nodes in a graph trajectory attached to run outputs."""
    from harnesslab.eval.trajectory import _flatten_steps

    nodes = _flatten_steps(run_output_field(outputs, "graph_trajectory", {}))
    return len([node for node in nodes if node in {"agent", "tools"}])
