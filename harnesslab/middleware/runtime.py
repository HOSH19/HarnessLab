"""Per-run mutable state for tool middleware (cache, circuit breaker)."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

_run_context: ContextVar[dict[str, Any] | None] = ContextVar("harnesslab_run_context", default=None)


def init_run_context() -> dict[str, Any]:
    """Create and bind a fresh tool middleware context for one graph invoke."""
    context: dict[str, Any] = {
        "tool_cache": {},
        "circuit_failures": {},
        "circuit_open": set(),
    }
    _run_context.set(context)
    return context


def get_run_context() -> dict[str, Any]:
    """Return the active run context, creating one if missing."""
    context = _run_context.get()
    if context is None:
        return init_run_context()
    return context


def clear_run_context() -> None:
    """Drop the active run context after invoke completes."""
    _run_context.set(None)
