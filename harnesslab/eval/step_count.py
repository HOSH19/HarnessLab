"""Step-count efficiency evaluator for Langfuse experiments.

Normalizes child run count against per-task expected_max_steps.
Tighter than the generic efficiency scorer thresholds.
"""

from harnesslab.eval.run_metrics import run_child_count, trajectory_agent_tool_steps


def step_count(run, example) -> dict:
    """Score run step count against a per-task maximum.

    Args:
        run: Run-like object with child run metadata.
        example: Dataset example with optional expected_max_steps.

    Returns:
        Dict with normalized step efficiency score and metadata comment.
    """
    reference = example.outputs or {}
    expected_max = int(reference.get("expected_max_steps", 12))
    outputs = getattr(run, "outputs", None) or {}
    child_count = run_child_count(run)
    graph_steps = trajectory_agent_tool_steps(outputs)
    steps = graph_steps if child_count <= 1 else child_count

    if steps <= expected_max:
        score = 1.0
    else:
        score = max(0.0, round(expected_max / steps, 2))

    return {
        "key": "step_count",
        "score": score,
        "comment": f"steps={steps}, graph_steps={graph_steps}, expected_max={expected_max}",
    }
