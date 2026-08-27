"""Execution limit helpers for graph compilation.

Maps execution harness config to LangGraph compile options.
Does not implement routing or middleware nodes.
"""

from harnesslab.config.models import ExecutionConfig


def recursion_limit(config: ExecutionConfig) -> int:
    """Derive LangGraph recursion_limit from harness execution config.

    Args:
        config: Execution harness configuration.

    Returns:
        Integer recursion limit for graph.compile().
    """
    return config.max_turns
