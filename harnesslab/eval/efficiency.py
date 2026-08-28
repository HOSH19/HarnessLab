"""Efficiency metrics from run metadata."""

from harnesslab.eval.run_metrics import run_child_count, run_latency_seconds, run_total_tokens
from harnesslab.eval.types import EvalExample, EvalRun


def efficiency(run: EvalRun, example: EvalExample) -> dict:
    """Score agent efficiency from run metadata."""
    reference = example.outputs or {}
    expected_max_steps = int(reference.get("expected_max_steps", 12))
    outputs = run.outputs or {}
    latency_ms = outputs.get("_latency_ms")
    if latency_ms is None:
        latency_ms = run_latency_seconds(run) * 1000
    else:
        latency_ms = float(latency_ms)
    tokens = outputs.get("_total_tokens")
    if tokens is None:
        tokens = run_total_tokens(run)
    else:
        tokens = int(tokens)
    child_count = run_child_count(run)

    score = 1.0
    if latency_ms > 20_000:
        score -= 0.3
    if tokens > 3000:
        score -= 0.3
    if child_count > expected_max_steps:
        score -= 0.2

    score = max(0.0, score)
    return {
        "key": "efficiency",
        "score": score,
        "comment": f"latency_ms={latency_ms:.0f}, tokens={tokens}, steps={child_count}",
    }
