"""Plan → execute → critic / replan topology."""

from typing import Any, Literal

from langchain_core.messages import AIMessage
from langgraph.graph import END, StateGraph

from harnesslab.graph.roles import make_role_node, resolve_role_prompt
from harnesslab.graph.state import AgentState
from harnesslab.graph.topologies._common import (
    add_agent_tool_stage,
    compile_graph,
    set_entry,
    tools_for_group,
    wrap_tools_node,
)
from harnesslab.graph.topologies.context import TopologyContext

_DEFAULTS = {
    "planner": (
        "You are the planner. Write a short numbered plan for investigating the "
        "incident and producing classify + draft_reply. Put the plan in your message. "
        "Do not call tools."
    ),
    "executor": (
        "You are the executor. Follow the plan. Use tools as needed. "
        "You MUST call classify and draft_reply before finishing."
    ),
    "critic": (
        "You are the critic. If classify and draft_reply were completed with a coherent "
        "update, reply with exactly PASS. Otherwise reply with REPLANN and one sentence "
        "on what is missing. Do not call tools."
    ),
}


def _capture_plan(state: AgentState) -> dict:
    """Store the latest assistant message as the plan string."""
    messages = state.get("messages", [])
    plan = ""
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content:
            plan = str(message.content)
            break
        if isinstance(message, dict) and message.get("content"):
            plan = str(message["content"])
            break
    return {"plan": plan, "stage": "planner"}


def _after_critic(state: AgentState) -> Literal["end", "replan"]:
    """End when the critic message starts with PASS; otherwise replan."""
    messages = state.get("messages", [])
    text = ""
    if messages:
        last = messages[-1]
        text = str(
            getattr(last, "content", None)
            or (last.get("content") if isinstance(last, dict) else "")
            or ""
        )
    if text.strip().upper().startswith("PASS"):
        return "end"
    return "replan"


def compile_plan_execute(ctx: TopologyContext) -> Any:
    """Compile planner → executor loop → critic with optional replan edge."""
    roles = ctx.graph.roles
    execute_tools = tools_for_group(ctx.tools, ctx.tool_groups, "execute")

    graph = StateGraph(AgentState)
    graph.add_node(
        "planner",
        make_role_node(
            system_prompt=resolve_role_prompt(roles, "planner", _DEFAULTS),
            tools=None,
            stage="planner",
        ),
    )
    graph.add_node("capture_plan", _capture_plan)
    graph.add_edge("planner", "capture_plan")
    graph.add_edge("capture_plan", "executor")

    add_agent_tool_stage(
        graph,
        agent_name="executor",
        tools_name="executor_tools",
        agent_node=make_role_node(
            system_prompt=resolve_role_prompt(roles, "executor", _DEFAULTS),
            tools=execute_tools,
            stage="executor",
        ),
        tools_node=wrap_tools_node(execute_tools, ctx.harness),
        next_node="critic",
    )

    graph.add_node(
        "critic",
        make_role_node(
            system_prompt=resolve_role_prompt(roles, "critic", _DEFAULTS),
            tools=None,
            stage="critic",
        ),
    )
    graph.add_conditional_edges(
        "critic",
        _after_critic,
        {"end": END, "replan": "planner"},
    )

    set_entry(graph, ctx.harness, "planner")
    return compile_graph(graph)
