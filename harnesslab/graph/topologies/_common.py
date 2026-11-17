"""Shared helpers for multi-node topology compilation."""

from collections.abc import Callable
from typing import Any, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from harnesslab.config.models import HarnessConfig
from harnesslab.graph.edges import should_continue
from harnesslab.graph.extract import extract_fields_from_messages
from harnesslab.graph.state import AgentState
from harnesslab.middleware.context import make_trim_node
from harnesslab.middleware.retry import make_retry_wrapper
from harnesslab.middleware.tools import make_tools_node, prepare_tools


def tools_for_group(ctx_tools: list[Any], groups: dict[str, list[Any]] | None, key: str) -> list[Any]:
    """Return a tool subgroup when configured, else the full tool list."""
    if groups and key in groups:
        return groups[key]
    return ctx_tools


def wrap_tools_node(tools: list[Any], harness: HarnessConfig) -> Callable:
    """Prepare tools and optionally wrap the tools node with retry middleware."""
    wrapped = prepare_tools(tools, harness)
    node = make_tools_node(wrapped)
    if harness.tooling.retry_count > 0:
        node = make_retry_wrapper(node, harness.tooling)
    return node


def set_entry(graph: StateGraph, harness: HarnessConfig, entry: str) -> None:
    """Apply optional trim_context entry, otherwise start at ``entry``."""
    if harness.context.history_limit is not None:
        graph.add_node("trim_context", make_trim_node(harness.context))
        graph.add_edge("trim_context", entry)
        graph.set_entry_point("trim_context")
    else:
        graph.set_entry_point(entry)


def compile_graph(graph: StateGraph) -> Any:
    """Compile with an in-memory checkpointer for trajectory extraction."""
    return graph.compile(checkpointer=MemorySaver())


def route_tools_or(next_node: str) -> Callable[[AgentState], Literal["tools", "next"]]:
    """Route to tools when the last message has tool calls, else ``next_node``."""

    def _route(state: AgentState) -> Literal["tools", "next"]:
        if should_continue(state) == "tools":
            return "tools"
        return "next"

    _route.__name__ = f"route_tools_or_{next_node}"
    return _route


def make_verifier_node() -> Callable[[AgentState], dict]:
    """Pass when classify + draft_reply appear in messages; else fail for retry."""

    def verify(state: AgentState) -> dict:
        parsed = extract_fields_from_messages(state.get("messages", []))
        ok = bool(parsed.get("classification") and parsed.get("final_reply"))
        return {
            "verification": "pass" if ok else "fail",
            "stage": "verify",
            "classification": parsed.get("classification") or state.get("classification", ""),
            "final_reply": parsed.get("final_reply") or state.get("final_reply", ""),
        }

    return verify


def after_verify(state: AgentState) -> Literal["end", "retry"]:
    """End on verifier pass; otherwise send work back for another finalize pass."""
    if state.get("verification") == "pass":
        return "end"
    return "retry"


def add_agent_tool_stage(
    graph: StateGraph,
    *,
    agent_name: str,
    tools_name: str,
    agent_node: Callable,
    tools_node: Callable,
    next_node: str,
) -> None:
    """Wire agent ↔ tools with exit to ``next_node`` when the agent stops calling tools."""
    graph.add_node(agent_name, agent_node)
    graph.add_node(tools_name, tools_node)
    graph.add_conditional_edges(
        agent_name,
        route_tools_or(next_node),
        {"tools": tools_name, "next": next_node},
    )
    graph.add_edge(tools_name, agent_name)
