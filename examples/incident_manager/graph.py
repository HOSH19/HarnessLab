"""Build and compile the incident manager LangGraph for a harness / graph variant."""

from examples.incident_manager.nodes import call_model
from examples.incident_manager.tools import (
    TOOLS,
    classify,
    correlate_timeline,
    draft_reply,
    fetch_metrics,
    read_incident,
    search_runbooks,
)
from harnesslab.config.graph_models import GraphConfig
from harnesslab.config.models import HarnessConfig
from harnesslab.examples.agent_graph import compile_agent_graph

TOOL_GROUPS = {
    "gather": [read_incident, fetch_metrics, search_runbooks, correlate_timeline],
    "analyze": [fetch_metrics, search_runbooks, correlate_timeline, classify],
    "finalize": [classify, draft_reply],
    "intake": [read_incident],
    "metrics": [fetch_metrics],
    "runbooks": [search_runbooks],
    "timeline": [correlate_timeline],
    "execute": TOOLS,
}


def build_graph(harness: HarnessConfig, graph: GraphConfig | None = None):
    """Compile the incident manager agent with harness + optional topology."""
    return compile_agent_graph(
        harness,
        call_model=call_model,
        tools=TOOLS,
        graph=graph,
        tool_groups=TOOL_GROUPS,
    )
