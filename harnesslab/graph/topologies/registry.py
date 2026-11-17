"""Dispatch GraphConfig.topology to the matching compiler."""

from typing import Any

from harnesslab.graph.topologies.context import TopologyContext
from harnesslab.graph.topologies.pipeline import compile_pipeline
from harnesslab.graph.topologies.plan_execute import compile_plan_execute
from harnesslab.graph.topologies.react import compile_react
from harnesslab.graph.topologies.supervisor import compile_supervisor

_BUILDERS = {
    "react": compile_react,
    "pipeline": compile_pipeline,
    "supervisor": compile_supervisor,
    "plan_execute": compile_plan_execute,
}


def build_topology(ctx: TopologyContext) -> Any:
    """Compile a harnessed graph for ``ctx.graph.topology``."""
    topology = ctx.graph.topology
    builder = _BUILDERS.get(topology)
    if builder is None:
        raise ValueError(f"Unknown topology: {topology}")
    return builder(ctx)


# Re-export for callers that import from registry historically.
__all__ = ["TopologyContext", "build_topology"]
