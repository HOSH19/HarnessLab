"""Apply cache and circuit-breaker behavior to a single tool call."""

from __future__ import annotations

import functools
from typing import Any

from langchain_core.runnables import RunnableConfig

from harnesslab.config.models import HarnessConfig
from harnesslab.middleware.cache import cache_key, get_cached_result, store_cached_result
from harnesslab.middleware.circuit_breaker import (
    CircuitOpenError,
    is_circuit_open,
    record_tool_failure,
    record_tool_success,
)
from harnesslab.middleware.runtime import get_run_context


def invoke_with_middleware(
    original: Any,
    *,
    tool_name: str,
    harness: HarnessConfig,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    """Run a tool callable through cache and circuit-breaker policies."""
    threshold = harness.tooling.circuit_breaker_threshold
    use_cache = harness.tooling.cache_reads
    context = get_run_context()
    key = cache_key(tool_name, args, kwargs)

    if use_cache:
        cached = get_cached_result(tool_name, key, context)
        if cached is not None:
            return cached

    if threshold is not None and is_circuit_open(tool_name, context):
        raise CircuitOpenError(tool_name)

    try:
        result = original(*args, **kwargs)
    except Exception:
        if threshold is not None:
            record_tool_failure(tool_name, context, threshold=threshold)
        raise

    if threshold is not None:
        record_tool_success(tool_name, context)
    if use_cache:
        store_cached_result(tool_name, key, result, context)
    return result


def wrap_tool(tool: Any, harness: HarnessConfig) -> Any:
    """Return a tool copy whose callable runs through harness middleware."""
    if not hasattr(tool, "func"):
        return tool

    tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", "tool")
    original = tool.func

    @functools.wraps(original)
    def wrapped(*args: Any, config: RunnableConfig | None = None, **kwargs: Any) -> Any:
        del config
        return invoke_with_middleware(
            original,
            tool_name=tool_name,
            harness=harness,
            args=args,
            kwargs=kwargs,
        )

    if hasattr(tool, "model_copy"):
        copy_tool = tool.model_copy(deep=True)
        copy_tool.func = wrapped  # type: ignore[attr-defined]
        return copy_tool

    tool.func = wrapped  # type: ignore[attr-defined]
    return tool
