"""Shared graph compilation for example agents."""

from collections.abc import Callable
from typing import Any

from langgraph.graph import StateGraph

from harnesslab.config.models import HarnessConfig
from harnesslab.graph.builder import compile_harnessed_graph
from harnesslab.graph.state import AgentState
from harnesslab.middleware.retry import make_retry_wrapper
from harnesslab.middleware.tools import make_tools_node, prepare_tools


def compile_agent_graph(
    harness: HarnessConfig,
    *,
    call_model: Callable[[AgentState], dict],
    tools: list[Any],
) -> Any:
    """Compile an example agent graph with harness middleware applied."""
    wrapped_tools = prepare_tools(tools, harness)
    tools_node = make_tools_node(wrapped_tools)
    if harness.tooling.retry_count > 0:
        tools_node = make_retry_wrapper(tools_node, harness.tooling)

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tools_node)

    return compile_harnessed_graph(
        graph,
        harness,
        agent_node="agent",
        tools_node="tools",
        require_complete_pipeline=True,
    )
