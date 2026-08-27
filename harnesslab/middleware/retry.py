"""Tool invocation retry middleware for LangGraph tool nodes.

Wraps a tool executor with configurable retry behavior.
Does not modify tool definitions or agent prompts.
"""

from collections.abc import Callable

from harnesslab.config.models import ToolingConfig
from harnesslab.graph.state import AgentState


def make_retry_wrapper(
    tool_node: Callable[[AgentState], dict],
    config: ToolingConfig,
) -> Callable[[AgentState], dict]:
    """Wrap a tool node with retry logic on failure.

    Args:
        tool_node: Base tool node function to wrap.
        config: Tooling harness configuration with retry_count.

    Returns:
        Wrapped node function that retries on exceptions.
    """
    retries = config.retry_count

    def retrying_tool_node(state: AgentState) -> dict:
        """Execute tools with up to retry_count attempts on error."""
        last_error: Exception | None = None
        attempts = retries + 1

        for _ in range(attempts):
            try:
                return tool_node(state)
            except Exception as exc:
                last_error = exc
                state = {
                    **state,
                    "error_count": state.get("error_count", 0) + 1,
                }

        if last_error is not None:
            raise last_error
        return {}

    return retrying_tool_node
