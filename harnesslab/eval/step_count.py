"""Step-count efficiency evaluator for experiment runs."""

from harnesslab.eval.run_metrics import run_child_count
from harnesslab.eval.types import EvalExample, EvalRun


def step_count(run: EvalRun, example: EvalExample) -> dict:
    """Score run step count against a per-task maximum."""
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
