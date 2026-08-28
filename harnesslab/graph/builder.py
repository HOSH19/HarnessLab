"""Assemble and compile LangGraph agents with harness middleware.

Reads HarnessConfig and injects middleware nodes into a base graph.
Does not define agent tools or business logic.
"""

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from harnesslab.config.models import HarnessConfig
from harnesslab.graph.edges import should_continue
from harnesslab.graph.pipeline import nudge_incomplete_pipeline, should_continue_with_nudge
from harnesslab.middleware.context import make_trim_node


def compile_harnessed_graph(
    base_graph: StateGraph,
    harness: HarnessConfig,
    *,
    agent_node: str = "agent",
    tools_node: str = "tools",
    require_complete_pipeline: bool = False,
) -> Any:
    """Compile a base graph with harness middleware applied.

    Args:
        base_graph: StateGraph with agent and tools nodes already added.
        harness: Harness configuration to apply.
        agent_node: Name of the LLM agent node in the graph.
        tools_node: Name of the tool execution node in the graph.

    Returns:
        Compiled LangGraph runnable with MemorySaver checkpointer.
    """
    graph = base_graph

    if harness.context.history_limit is not None:
        trim_node = make_trim_node(harness.context)
        graph.add_node("trim_context", trim_node)
        graph.add_edge("trim_context", agent_node)
        graph.set_entry_point("trim_context")
    else:
        graph.set_entry_point(agent_node)

    if require_complete_pipeline:
        graph.add_node("nudge", nudge_incomplete_pipeline)
        graph.add_conditional_edges(
            agent_node,
            should_continue_with_nudge,
            {"tools": tools_node, "nudge": "nudge", "end": END},
        )
        graph.add_edge("nudge", agent_node)
    else:
        graph.add_conditional_edges(agent_node, should_continue, {"tools": tools_node, "end": END})
    graph.add_edge(tools_node, agent_node)

    return graph.compile(checkpointer=MemorySaver())
