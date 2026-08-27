"""Routing helpers for LangGraph conditional edges.

Determines whether the agent loop should continue to tools or end.
Owned by graph layer; does not contain harness middleware logic.
"""

from typing import Literal

from langchain_core.messages import AIMessage

from harnesslab.graph.state import AgentState


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """Route to tools if the last message has tool calls, otherwise end.

    Args:
        state: Current graph state with message history.

    Returns:
        Next edge target: "tools" or "end".
    """
    messages = state.get("messages", [])
    if not messages:
        return "end"

    last = messages[-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return "end"
