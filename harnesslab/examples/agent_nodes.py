"""Shared LangGraph node factories for example agents."""

import os
from collections.abc import Callable
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode

from harnesslab.config.model_catalog import DEFAULT_MODEL
from harnesslab.graph.state import AgentState


def make_agent_nodes(
    *,
    system_prompt: str,
    tools: list[Any],
) -> tuple[Callable[[AgentState], dict], Callable[[AgentState, RunnableConfig | None], dict]]:
    """Return call_model and call_tools nodes for a tool-using agent."""

    def call_model(state: AgentState) -> dict:
        """Invoke the LLM with tool binding on current messages."""
        model_name = os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)
        llm = ChatOpenAI(model=model_name, temperature=0).bind_tools(tools)
        messages = [SystemMessage(content=system_prompt), *state["messages"]]
        response = llm.invoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    def call_tools(state: AgentState, config: RunnableConfig | None = None) -> dict:
        """Execute tool calls from the latest assistant message."""
        return tool_node.invoke(state, config)

    return call_model, call_tools
