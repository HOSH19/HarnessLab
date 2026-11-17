"""Supervisor + specialist worker topology."""

from typing import Any

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
    "intake": (
        "You are intake. Read the incident and gather the base ticket facts. "
        "Call read tools as needed. Do not classify or draft yet."
    ),
    "metrics_worker": (
        "You are the metrics specialist. Fetch and interpret live metrics for the incident. "
        "Summarize findings briefly in your final assistant message. Do not classify or draft."
    ),
    "runbooks_worker": (
        "You are the runbooks specialist. Search runbooks for remediation guidance. "
        "Summarize findings briefly. Do not classify or draft."
    ),
    "timeline_worker": (
        "You are the timeline specialist. Correlate deployment and alert events. "
        "Summarize the sequence. Do not classify or draft."
    ),
    "synthesize": (
        "You are the supervisor synthesizer. Merge specialist findings into a coherent "
        "root-cause hypothesis. Do not call tools; write a short synthesis."
    ),
    "finalize": (
        "You are finalize. You MUST call classify and draft_reply as tools before finishing. "
        "Use the synthesis and evidence already in the conversation."
    ),
}


def _record_worker(worker_name: str):
    """Append a worker completion marker into shared state."""

    def _node(state: AgentState) -> dict:
        return {
            "worker_results": [worker_name],
            "stage": worker_name,
        }

    return _node


def compile_supervisor(ctx: TopologyContext) -> Any:
    """Compile intake → specialist workers → synthesize → finalize.

    Workers run in a fixed declared order (parent keeps control). This is
    graph engineering with role isolation, not free-form agent handoffs.
    """
    roles = ctx.graph.roles
    intake_tools = tools_for_group(ctx.tools, ctx.tool_groups, "intake")
    metrics_tools = tools_for_group(ctx.tools, ctx.tool_groups, "metrics")
    runbooks_tools = tools_for_group(ctx.tools, ctx.tool_groups, "runbooks")
    timeline_tools = tools_for_group(ctx.tools, ctx.tool_groups, "timeline")
    finalize_tools = tools_for_group(ctx.tools, ctx.tool_groups, "finalize")

    graph = StateGraph(AgentState)

    add_agent_tool_stage(
        graph,
        agent_name="intake",
        tools_name="intake_tools",
        agent_node=make_role_node(
            system_prompt=resolve_role_prompt(roles, "intake", _DEFAULTS),
            tools=intake_tools,
            stage="intake",
        ),
        tools_node=wrap_tools_node(intake_tools, ctx.harness),
        next_node="metrics_worker",
    )
    add_agent_tool_stage(
        graph,
        agent_name="metrics_worker",
        tools_name="metrics_tools",
        agent_node=make_role_node(
            system_prompt=resolve_role_prompt(roles, "metrics_worker", _DEFAULTS),
            tools=metrics_tools,
            stage="metrics_worker",
        ),
        tools_node=wrap_tools_node(metrics_tools, ctx.harness),
        next_node="mark_metrics",
    )
    graph.add_node("mark_metrics", _record_worker("metrics"))
    graph.add_edge("mark_metrics", "runbooks_worker")

    add_agent_tool_stage(
        graph,
        agent_name="runbooks_worker",
        tools_name="runbooks_tools",
        agent_node=make_role_node(
            system_prompt=resolve_role_prompt(roles, "runbooks_worker", _DEFAULTS),
            tools=runbooks_tools,
            stage="runbooks_worker",
        ),
        tools_node=wrap_tools_node(runbooks_tools, ctx.harness),
        next_node="mark_runbooks",
    )
    graph.add_node("mark_runbooks", _record_worker("runbooks"))
    graph.add_edge("mark_runbooks", "timeline_worker")

    add_agent_tool_stage(
        graph,
        agent_name="timeline_worker",
        tools_name="timeline_tools",
        agent_node=make_role_node(
            system_prompt=resolve_role_prompt(roles, "timeline_worker", _DEFAULTS),
            tools=timeline_tools,
            stage="timeline_worker",
        ),
        tools_node=wrap_tools_node(timeline_tools, ctx.harness),
        next_node="mark_timeline",
    )
    graph.add_node("mark_timeline", _record_worker("timeline"))
    graph.add_edge("mark_timeline", "synthesize")

    graph.add_node(
        "synthesize",
        make_role_node(
            system_prompt=resolve_role_prompt(roles, "synthesize", _DEFAULTS),
            tools=None,
            stage="synthesize",
        ),
    )
    graph.add_edge("synthesize", "finalize")

    add_agent_tool_stage(
        graph,
        agent_name="finalize",
        tools_name="finalize_tools",
        agent_node=make_role_node(
            system_prompt=resolve_role_prompt(roles, "finalize", _DEFAULTS),
            tools=finalize_tools,
            stage="finalize",
        ),
        tools_node=wrap_tools_node(finalize_tools, ctx.harness),
        next_node=END,
    )

    set_entry(graph, ctx.harness, "intake")
    return compile_graph(graph)
