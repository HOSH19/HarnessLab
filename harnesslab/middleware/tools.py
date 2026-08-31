"""Build ToolNode instances with optional harness middleware."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode

from harnesslab.config.models import HarnessConfig
from harnesslab.graph.state import AgentState
from harnesslab.middleware.wrap import wrap_tool


def prepare_tools(tools: list[Any], harness: HarnessConfig) -> list[Any]:
    """Wrap tools with cache and circuit-breaker middleware when configured."""
    if not harness.tooling.cache_reads and harness.tooling.circuit_breaker_threshold is None:
        return tools
    return [wrap_tool(tool, harness) for tool in tools]


def make_tools_node(tools: list[Any]) -> Callable[[AgentState, Optional[RunnableConfig]], dict]:
    """Create a LangGraph-compatible tools node from a tool list."""
    tool_node = ToolNode(tools)

    def call_tools(state: AgentState, config: Optional[RunnableConfig] = None) -> dict:
        """Execute pending tool calls from the latest assistant message."""
        return tool_node.invoke(state, config)

    return call_tools
