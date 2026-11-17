"""Shared graph compilation for example agents."""

from collections.abc import Callable
from typing import Any

from harnesslab.config.graph_loader import default_react_graph
from harnesslab.config.graph_models import GraphConfig
from harnesslab.config.models import HarnessConfig
from harnesslab.graph.state import AgentState
from harnesslab.graph.topologies import TopologyContext, build_topology


def compile_agent_graph(
    harness: HarnessConfig,
    *,
    call_model: Callable[[AgentState], dict],
    tools: list[Any],
    graph: GraphConfig | None = None,
    role_prompts: dict[str, str] | None = None,
    tool_groups: dict[str, list[Any]] | None = None,
) -> Any:
    """Compile an example agent with a selected topology and harness middleware."""
    selected = graph or default_react_graph()
    ctx = TopologyContext(
        harness=harness,
        graph=selected,
        tools=tools,
        call_model=call_model,
        role_prompts=role_prompts or {},
        tool_groups=tool_groups,
    )
    return build_topology(ctx)
