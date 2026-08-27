"""Trim message history before model calls.

Implements the context harness layer as a graph node function.
Does not perform summarization or LLM-based compression.
"""

from harnesslab.config.models import ContextConfig
from harnesslab.graph.state import AgentState


def make_trim_node(config: ContextConfig):
    """Create a node that trims messages to history_limit.

    Args:
        config: Context harness configuration with optional history_limit.

    Returns:
        Node function compatible with StateGraph.add_node.
    """
    limit = config.history_limit

    def trim_messages(state: AgentState) -> dict:
        """Keep only the most recent messages when a limit is set."""
        if limit is None:
            return {}

        messages = state.get("messages", [])
        if len(messages) <= limit:
            return {}

        return {"messages": messages[-limit:]}

    return trim_messages
