"""TypedDict state schema for LangGraph agents.

Defines the shared state shape used by graph nodes and middleware.
Agent-specific fields are extended in example projects.
"""

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Base state passed between LangGraph nodes."""

    messages: Annotated[list, add_messages]
    ticket_id: str
    classification: str
    final_reply: str
    error_count: int
