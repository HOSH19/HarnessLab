"""Graph node functions for the research agent example."""

from examples.research_agent.rules import SYSTEM_PROMPT
from examples.research_agent.tools import TOOLS
from harnesslab.examples.agent_nodes import make_agent_nodes

call_model, call_tools = make_agent_nodes(system_prompt=SYSTEM_PROMPT, tools=TOOLS)
