"""USD cost estimation for LangSmith experiment runs."""

from __future__ import annotations

import os
from typing import Any

from harnesslab.config.model_catalog import DEFAULT_MODEL, model_cost_per_1k_tokens
from harnesslab.eval.outputs import run_output_field
from harnesslab.eval.run_metrics import run_total_tokens


def resolve_run_model(run: Any) -> str:
    """Read the model name from run metadata when available."""
    outputs = getattr(run, "outputs", None) or {}
    if isinstance(outputs, dict):
        model = run_output_field(outputs, "model")
        if model:
            return str(model)

    extra = getattr(run, "extra", None) or {}
    if isinstance(extra, dict):
        metadata = extra.get("metadata") or {}
        if isinstance(metadata, dict) and metadata.get("model"):
            return str(metadata["model"])
    return os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)


def estimate_run_cost_usd(run: Any) -> float:
    """Estimate run cost in USD from token usage and model pricing."""
    tokens = run_total_tokens(run)
    if tokens <= 0:
        return 0.0
    model = resolve_run_model(run)
    rate = model_cost_per_1k_tokens(model)
    return round((tokens / 1000.0) * rate, 6)
