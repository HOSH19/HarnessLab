"""Simulated flaky tool failures scoped per graph run.

Uses thread-local storage so attempt counts persist across tool invocations
within a single graph run, including LangChain tool wrappers and retries.
"""

from __future__ import annotations

import threading

_local = threading.local()


def init_flaky_tools(flaky_tools: dict[str, int] | None) -> None:
    """Reset flaky tool state for a new graph run."""
    _local.flaky = dict(flaky_tools or {})
    _local.attempts = {}


def _flaky_config() -> dict[str, int]:
    return getattr(_local, "flaky", {})


def _attempt_counts() -> dict[str, int]:
    if not hasattr(_local, "attempts"):
        _local.attempts = {}
    return _local.attempts


def maybe_fail(tool_name: str) -> None:
    """Raise when a tool should fail on the current attempt."""
    config = _flaky_config()
    if not config:
        return

    fail_times = config.get(tool_name, 0)
    if fail_times <= 0:
        return

    counts = _attempt_counts()
    attempt = counts.get(tool_name, 0) + 1
    counts[tool_name] = attempt

    if attempt <= fail_times:
        raise RuntimeError(
            f"Simulated flaky failure for {tool_name} (attempt {attempt}/{fail_times})"
        )


def attempt_count(tool_name: str) -> int:
    """Return how many times a tool has been invoked this run."""
    return _attempt_counts().get(tool_name, 0)
