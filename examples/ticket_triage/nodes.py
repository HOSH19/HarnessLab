"""Graph node functions for the ticket triage example agent.

Defines call_model and call_tools nodes. Prompt and model selection
live here; harness middleware is applied by graph.builder.
"""

import os

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode

from langchain_core.runnables import RunnableConfig

from examples.ticket_triage.tools import TOOLS
from harnesslab.graph.state import AgentState

SYSTEM_PROMPT = """You are a support ticket triage agent.

For each ticket:
1. read_ticket to fetch details
2. search_kb with keywords from the ticket
3. classify into account, billing, or technical
4. draft_reply referencing relevant KB guidance

Use tools in that order. Be concise."""


def _model() -> ChatOpenAI:
    """Create the chat model from environment configuration."""
    model_name = os.getenv("HARNESSLAB_MODEL", "gpt-4o-mini")
    return ChatOpenAI(model=model_name, temperature=0)


def call_model(state: AgentState) -> dict:
    """Invoke the LLM with tool binding on current messages.

    Args:
        state: Current graph state including message history.

    Returns:
        State update with a new assistant message.
    """
    llm = _model().bind_tools(TOOLS)
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    response = llm.invoke(messages)
    return {"messages": [response]}


_tool_node = ToolNode(TOOLS)


def call_tools(state: AgentState, config: RunnableConfig | None = None) -> dict:
    """Execute tool calls from the latest assistant message.

    Args:
        state: Current graph state with pending tool calls.
        config: LangGraph runnable config (passed through to ToolNode).

    Returns:
        State update with tool result messages.
    """
    return _tool_node.invoke(state, config)
