"""Efficiency metrics from run metadata.

Measures turns, latency, and token usage when available.
Does not invoke models or re-run agents.
"""

from harnesslab.eval.run_metrics import (
    run_child_count,
    run_latency_seconds,
    run_total_tokens,
    trajectory_agent_tool_steps,
)


def efficiency(run, example) -> dict:
    """Score agent efficiency from run metadata.

    Args:
        run: Run-like object with timing and token metadata.
        example: Dataset example with expected_max_steps reference.

    Returns:
        Dict with normalized efficiency score and metadata comment.
    """
    reference = example.outputs or {}
    expected_max_steps = int(reference.get("expected_max_steps", 12))
    outputs = getattr(run, "outputs", None) or {}
    latency_ms = run_latency_seconds(run) * 1000
    tokens = run_total_tokens(run)
    child_count = run_child_count(run)
    graph_steps = trajectory_agent_tool_steps(outputs)
    steps = graph_steps if child_count <= 1 else child_count

    score = 1.0
    if latency_ms > 6_000:
        score -= min(0.4, 0.1 * ((latency_ms - 6_000) / 2_000))
    if tokens > 1_500:
        score -= 0.2
    elif tokens == 0 and steps > expected_max_steps:
        score -= 0.1
    if steps > expected_max_steps:
        score -= min(0.3, 0.3 * (steps - expected_max_steps) / max(expected_max_steps, 1))

    score = max(0.0, round(score, 2))
    return {
        "key": "efficiency",
        "score": score,
        "comment": (
            f"latency_ms={latency_ms:.0f}, tokens={tokens}, "
            f"steps={steps}, graph_steps={graph_steps}"
        ),
    }
