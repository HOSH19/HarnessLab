"""Build and compile the incident manager LangGraph for a harness variant."""

from examples.incident_manager.nodes import call_model
from examples.incident_manager.tools import TOOLS
from harnesslab.config.models import HarnessConfig
from harnesslab.examples.agent_graph import compile_agent_graph


def build_graph(harness: HarnessConfig):
    """Compile the incident manager agent with a harness configuration."""
    return compile_agent_graph(harness, call_model=call_model, tools=TOOLS)
