"""Execution limit helpers for graph compilation.

Maps execution harness config to LangGraph compile options.
Does not implement routing or middleware nodes.
"""

from harnesslab.config.models import ExecutionConfig


def recursion_limit(config: ExecutionConfig) -> int:
    """Derive LangGraph recursion_limit from harness execution config.

    ``max_turns`` counts agent reasoning steps; LangGraph counts each node
    visit (agent and tools are separate supersteps), so we allocate two
    supersteps per configured turn.

    Args:
        config: Execution harness configuration.

    Returns:
        Integer recursion limit for graph.invoke().
    """
    return config.max_turns * 2
