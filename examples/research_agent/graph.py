"""Build and compile the research agent LangGraph for a harness / graph variant."""

from examples.research_agent.nodes import call_model
from examples.research_agent.tools import (
    TOOLS,
    classify,
    draft_reply,
    read_source,
    read_topic,
    search_literature,
)
from harnesslab.config.graph_models import GraphConfig
from harnesslab.config.models import HarnessConfig
from harnesslab.examples.agent_graph import compile_agent_graph

TOOL_GROUPS = {
    "gather": [read_topic, search_literature, read_source],
    "analyze": [search_literature, read_source, classify],
    "finalize": [classify, draft_reply],
    "intake": [read_topic],
    "metrics": [search_literature],
    "runbooks": [read_source],
    "timeline": [read_topic, search_literature],
    "execute": TOOLS,
}


def build_graph(harness: HarnessConfig, graph: GraphConfig | None = None):
    """Compile the research agent with harness + optional topology."""
    return compile_agent_graph(
        harness,
        call_model=call_model,
        tools=TOOLS,
        graph=graph,
        tool_groups=TOOL_GROUPS,
    )
