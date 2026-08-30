"""Graph node functions for the incident manager example agent."""

from examples.incident_manager.rules import SYSTEM_PROMPT
from examples.incident_manager.tools import TOOLS
from harnesslab.examples.agent_nodes import make_agent_nodes

call_model, call_tools = make_agent_nodes(system_prompt=SYSTEM_PROMPT, tools=TOOLS)
