"""Graph node functions for the incident analyst example agent."""

import os

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode

from examples.incident_analyst.rules import SYSTEM_PROMPT
from examples.incident_analyst.tools import TOOLS
from harnesslab.config.model_catalog import DEFAULT_MODEL
from harnesslab.graph.state import AgentState


def _model() -> ChatOpenAI:
    """Create the chat model from environment configuration."""
    model_name = os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)
    return ChatOpenAI(model=model_name, temperature=0)


def call_model(state: AgentState) -> dict:
    """Invoke the LLM with tool binding on current messages."""
    llm = _model().bind_tools(TOOLS)
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    response = llm.invoke(messages)
    return {"messages": [response]}


_tool_node = ToolNode(TOOLS)


def call_tools(state: AgentState, config: RunnableConfig | None = None) -> dict:
    """Execute tool calls from the latest assistant message."""
    return _tool_node.invoke(state, config)
