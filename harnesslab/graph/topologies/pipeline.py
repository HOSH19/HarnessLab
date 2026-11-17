"""Fixed-stage pipeline topology with optional verifier retry."""

from typing import Any

from langgraph.graph import END, StateGraph

from harnesslab.graph.roles import make_role_node, resolve_role_prompt
from harnesslab.graph.state import AgentState
from harnesslab.graph.topologies._common import (
    add_agent_tool_stage,
    after_verify,
    compile_graph,
    make_verifier_node,
    set_entry,
    tools_for_group,
    wrap_tools_node,
)
from harnesslab.graph.topologies.context import TopologyContext

_DEFAULTS = {
    "gather": (
        "You are the gather stage. Collect incident evidence with tools "
        "(read, metrics, runbooks, timeline as needed). Do not classify or draft yet."
    ),
    "analyze": (
        "You are the analyze stage. Reason about root cause from gathered evidence. "
        "You may call tools to fill gaps. Do not draft the stakeholder reply yet; "
        "you may call classify if ready."
    ),
    "finalize": (
        "You are the finalize stage. You MUST call classify and draft_reply as tools "
        "before finishing. Be concise and cite evidence."
    ),
}


def compile_pipeline(ctx: TopologyContext) -> Any:
    """Compile gather → analyze → finalize (+ optional verify→retry)."""
    roles = ctx.graph.roles
    gather_tools = tools_for_group(ctx.tools, ctx.tool_groups, "gather")
    analyze_tools = tools_for_group(ctx.tools, ctx.tool_groups, "analyze")
    finalize_tools = tools_for_group(ctx.tools, ctx.tool_groups, "finalize")

    gather = make_role_node(
        system_prompt=resolve_role_prompt(roles, "gather", _DEFAULTS),
        tools=gather_tools,
        stage="gather",
    )
    analyze = make_role_node(
        system_prompt=resolve_role_prompt(roles, "analyze", _DEFAULTS),
        tools=analyze_tools,
        stage="analyze",
    )
    finalize = make_role_node(
        system_prompt=resolve_role_prompt(roles, "finalize", _DEFAULTS),
        tools=finalize_tools,
        stage="finalize",
    )

    graph = StateGraph(AgentState)
    add_agent_tool_stage(
        graph,
        agent_name="gather",
        tools_name="gather_tools",
        agent_node=gather,
        tools_node=wrap_tools_node(gather_tools, ctx.harness),
        next_node="analyze",
    )
    add_agent_tool_stage(
        graph,
        agent_name="analyze",
        tools_name="analyze_tools",
        agent_node=analyze,
        tools_node=wrap_tools_node(analyze_tools, ctx.harness),
        next_node="finalize",
    )

    if ctx.graph.require_verifier:
        add_agent_tool_stage(
            graph,
            agent_name="finalize",
            tools_name="finalize_tools",
            agent_node=finalize,
            tools_node=wrap_tools_node(finalize_tools, ctx.harness),
            next_node="verify",
        )
        graph.add_node("verify", make_verifier_node())
        graph.add_conditional_edges(
            "verify",
            after_verify,
            {"end": END, "retry": "finalize"},
        )
    else:
        add_agent_tool_stage(
            graph,
            agent_name="finalize",
            tools_name="finalize_tools",
            agent_node=finalize,
            tools_node=wrap_tools_node(finalize_tools, ctx.harness),
            next_node=END,
        )

    set_entry(graph, ctx.harness, "gather")
    return compile_graph(graph)
