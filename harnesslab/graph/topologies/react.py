"""Single-agent ReAct loop topology (baseline)."""

from typing import Any

from langgraph.graph import StateGraph

from harnesslab.graph.builder import compile_harnessed_graph
from harnesslab.graph.state import AgentState
from harnesslab.graph.topologies.context import TopologyContext
from harnesslab.middleware.retry import make_retry_wrapper
from harnesslab.middleware.tools import make_tools_node, prepare_tools


def compile_react(ctx: TopologyContext) -> Any:
    """Compile the classic agent ↔ tools ReAct loop with harness middleware."""
    wrapped_tools = prepare_tools(ctx.tools, ctx.harness)
    tools_node = make_tools_node(wrapped_tools)
    if ctx.harness.tooling.retry_count > 0:
        tools_node = make_retry_wrapper(tools_node, ctx.harness.tooling)

    graph = StateGraph(AgentState)
    graph.add_node("agent", ctx.call_model)
    graph.add_node("tools", tools_node)

    return compile_harnessed_graph(
        graph,
        ctx.harness,
        agent_node="agent",
        tools_node="tools",
        require_complete_pipeline=True,
    )
