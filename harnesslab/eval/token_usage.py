"""Token usage helpers for local runs and LangSmith run objects."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage


def usage_dict_total_tokens(usage: dict[str, Any] | None) -> int:
    """Return total tokens from a single usage_metadata dict."""
    if not isinstance(usage, dict):
        return 0
    total = usage.get("total_tokens")
    if total is not None:
        return int(total)
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    return input_tokens + output_tokens


def aggregate_usage_metadata(usage_by_model: dict[str, Any] | None) -> tuple[int, str | None]:
    """Sum tokens across per-model usage metadata from a callback."""
    if not isinstance(usage_by_model, dict) or not usage_by_model:
        return 0, None

    total = 0
    primary_model: str | None = None
    primary_tokens = -1
    for model, usage in usage_by_model.items():
        model_tokens = usage_dict_total_tokens(usage)
        total += model_tokens
        if model_tokens > primary_tokens:
            primary_tokens = model_tokens
            primary_model = str(model)

    if len(usage_by_model) == 1:
        primary_model = next(iter(usage_by_model))

    return total, primary_model


def message_tokens(messages: list[Any]) -> int:
    """Sum token usage recorded on AIMessage objects in graph state."""
    total = 0
    for message in messages:
        if not isinstance(message, AIMessage):
            continue
        usage = getattr(message, "usage_metadata", None)
        total += usage_dict_total_tokens(usage)
    return total
