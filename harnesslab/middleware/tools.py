"""Compose per-tool middleware (cache, circuit breaker) for ToolNode."""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode

from harnesslab.config.models import HarnessConfig
from harnesslab.graph.state import AgentState
from harnesslab.middleware.cache import (
    cache_key,
    get_cached_result,
    store_cached_result,
)
from harnesslab.middleware.circuit_breaker import (
    CircuitOpenError,
    is_circuit_open,
    record_tool_failure,
    record_tool_success,
)
from harnesslab.middleware.runtime import get_run_context


def _tool_name(tool: Any) -> str:
    return getattr(tool, "name", None) or getattr(tool, "__name__", "tool")


def _wrap_tool_callable(tool: Any, harness: HarnessConfig) -> Any:
    """Return a copy of a LangChain tool with harness middleware on its callable."""
    tool_name = _tool_name(tool)
    threshold = harness.tooling.circuit_breaker_threshold
    use_cache = harness.tooling.cache_reads

    if not hasattr(tool, "func"):
        return tool

    original = tool.func

    @functools.wraps(original)
    def wrapped(*args: Any, config: RunnableConfig | None = None, **kwargs: Any) -> Any:
        del config
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

    if hasattr(tool, "model_copy"):
        copy_tool = tool.model_copy(deep=True)
        copy_tool.func = wrapped  # type: ignore[attr-defined]
        return copy_tool

    tool.func = wrapped  # type: ignore[attr-defined]
    return tool


def prepare_tools(tools: list[Any], harness: HarnessConfig) -> list[Any]:
    """Return tools wrapped with cache and circuit-breaker middleware when configured."""
    if not harness.tooling.cache_reads and harness.tooling.circuit_breaker_threshold is None:
        return tools
    return [_wrap_tool_callable(tool, harness) for tool in tools]


def make_tools_node(tools: list[Any]) -> Callable[[AgentState, RunnableConfig | None], dict]:
    """Build a graph tools node from a tool list."""
    tool_node = ToolNode(tools)

    def call_tools(state: AgentState, config: RunnableConfig | None = None) -> dict:
        return tool_node.invoke(state, config)

    return call_tools
