"""Lightweight types for evaluator functions (Langfuse-compatible)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvalRun:
    """Minimal run view passed to scorers."""

    outputs: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    child_runs: list[Any] = field(default_factory=list)

    @classmethod
    def from_output(cls, output: dict[str, Any] | None) -> EvalRun:
        """Build a run view from a task return dict."""
        payload = dict(output or {})
        child_count = int(payload.pop("_child_count", 0) or 0)
        error = payload.pop("_error", None)
        return cls(
            outputs=payload,
            error=str(error) if error is not None else None,
            child_runs=[None] * child_count,
        )


@dataclass
class EvalExample:
    """Minimal dataset example view passed to scorers."""

    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_item(cls, *, input: Any, expected_output: Any) -> EvalExample:
        """Build an example view from Langfuse experiment item fields."""
        return cls(
            inputs=dict(input or {}),
            outputs=dict(expected_output or {}),
        )
