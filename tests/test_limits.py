"""Execution limit helper tests."""

from harnesslab.config.models import ExecutionConfig
from harnesslab.middleware.limits import recursion_limit


def test_recursion_limit_doubles_agent_turns() -> None:
    """LangGraph supersteps include both agent and tools nodes per turn."""
    config = ExecutionConfig(max_turns=10)
    assert recursion_limit(config) == 20
