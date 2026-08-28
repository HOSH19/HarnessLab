"""Efficiency metrics from LangSmith run metadata.

Measures turns, latency, and token usage when available.
Does not invoke models or re-run agents.
"""

from langsmith.schemas import Example, Run

from harnesslab.eval.run_metrics import run_child_count, run_latency_seconds, run_total_tokens


def efficiency(run: Run, example: Example) -> dict:
    """Score agent efficiency from run metadata.

    Args:
        run: LangSmith run with timing and token metadata.
        example: Dataset example (unused, required by LangSmith API).

    Returns:
        Dict with normalized efficiency score and metadata comment.
    """
    _ = example
    latency_ms = run_latency_seconds(run) * 1000
    tokens = run_total_tokens(run)
    child_count = run_child_count(run)

    score = 1.0
    if latency_ms > 30_000:
        score -= 0.3
    if tokens > 4000:
        score -= 0.3
    if child_count > 20:
        score -= 0.2

    score = max(0.0, score)
    return {
        "key": "efficiency",
        "score": score,
        "comment": f"latency_ms={latency_ms:.0f}, tokens={tokens}, steps={child_count}",
    }
