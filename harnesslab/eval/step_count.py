"""Step-count efficiency evaluator for LangSmith experiments.

Normalizes child run count against per-task expected_max_steps.
Tighter than the generic efficiency scorer thresholds.
"""

from langsmith.schemas import Example, Run

from harnesslab.eval.run_metrics import run_child_count


def step_count(run: Run, example: Example) -> dict:
    """Score run step count against a per-task maximum.

    Args:
        run: LangSmith run with child run metadata.
        example: Dataset example with optional expected_max_steps.

    Returns:
        Dict with normalized step efficiency score and metadata comment.
    """
    reference = example.outputs or {}
    expected_max = int(reference.get("expected_max_steps", 12))
    child_count = run_child_count(run)

    if child_count <= expected_max:
        score = 1.0
    else:
        score = max(0.0, expected_max / child_count)

    return {
        "key": "step_count",
        "score": score,
        "comment": f"steps={child_count}, expected_max={expected_max}",
    }
