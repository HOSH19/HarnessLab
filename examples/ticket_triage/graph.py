"""Build and compile the ticket triage LangGraph for a harness variant.

Creates the base StateGraph and delegates harness middleware to
harnesslab.graph.builder. Does not run experiments.
"""

from langgraph.graph import StateGraph

from examples.ticket_triage.nodes import call_model, call_tools
from harnesslab.config.models import HarnessConfig
from harnesslab.graph.builder import compile_harnessed_graph
from harnesslab.graph.state import AgentState
from harnesslab.middleware.retry import make_retry_wrapper


def build_ticket_triage_graph(harness: HarnessConfig):
    """Compile the ticket triage agent with a harness configuration.

    Args:
        harness: Harness variant to apply.

    Returns:
        Compiled LangGraph runnable with checkpointer.
    """
    tools_node = call_tools
    if harness.tooling.retry_count > 0:
        tools_node = make_retry_wrapper(call_tools, harness.tooling)

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
