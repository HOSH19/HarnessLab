"""Helpers for reading normalized fields from LangSmith run outputs."""

from typing import Any


def run_output_field(outputs: dict[str, Any] | None, key: str, default: Any = None) -> Any:
    """Read a field from flat or nested ``details`` run outputs."""
    if not outputs:
        return default
    if key in outputs and outputs[key] not in (None, ""):
        return outputs[key]
    details = outputs.get("details") or {}
    if isinstance(details, dict) and key in details:
        return details[key]
    return default
