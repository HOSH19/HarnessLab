"""Shared role-node helpers for multi-node topologies."""

import os
from collections.abc import Callable
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from harnesslab.config.model_catalog import DEFAULT_MODEL
from harnesslab.graph.state import AgentState


def make_role_node(
    *,
    system_prompt: str,
    tools: list[Any] | None = None,
    stage: str | None = None,
) -> Callable[[AgentState], dict]:
    """Return an LLM node optionally bound to tools and tagging ``stage``."""

    def call_role(state: AgentState) -> dict:
        model_name = os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)
        llm = ChatOpenAI(model=model_name, temperature=0)
        if tools:
            llm = llm.bind_tools(tools)
        messages = [SystemMessage(content=system_prompt), *state["messages"]]
        response = llm.invoke(messages)
        update: dict[str, Any] = {"messages": [response]}
        if stage is not None:
            update["stage"] = stage
        return update

    return call_role


def resolve_role_prompt(
    graph_roles: dict[str, str],
    role: str,
    defaults: dict[str, str],
) -> str:
    """Prefer graph YAML role override, else example default prompt."""
    return graph_roles.get(role) or defaults.get(role) or defaults.get("default", "")
