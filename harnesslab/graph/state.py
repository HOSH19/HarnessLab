"""TypedDict state schema for LangGraph agents.

Defines the shared state shape used by graph nodes and middleware.
Agent-specific fields are extended in example projects.
"""

from operator import add
from typing import Annotated, NotRequired, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Base state passed between LangGraph nodes."""

    messages: Annotated[list, add_messages]
    ticket_id: str
    classification: str
    final_reply: str
    error_count: int
    plan: NotRequired[str]
    worker_results: NotRequired[Annotated[list, add]]
    verification: NotRequired[str]
    stage: NotRequired[str]
