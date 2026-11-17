"""Coordination evaluator — required stage subsequence from trajectory."""

from langsmith.schemas import Example, Run

from harnesslab.eval.outputs import run_output_field
from harnesslab.eval.sequence import subsequence_progress
from harnesslab.eval.trajectory import flatten_trajectory_steps


def coordination_pass(run: Run, example: Example) -> dict:
    """Score whether required coordination stages appear in order.

    Reads ``required_stages`` from the example outputs (preferred) or falls
    back to ``expected_nodes``. Missing expectations score 1.0 (skipped).
    """
    outputs = run.outputs or {}
    reference = example.outputs or {}
    required = reference.get("required_stages") or reference.get("expected_nodes") or []
    trajectory = run_output_field(outputs, "graph_trajectory", {})
    actual_nodes = flatten_trajectory_steps(trajectory)

    if not required:
        return {
            "key": "coordination_pass",
            "score": 1.0,
            "comment": "skipped=no_required_stages",
        }

    score = subsequence_progress(required, actual_nodes)
    return {
        "key": "coordination_pass",
        "score": score,
        "comment": f"progress={score:.2f}, required={required}, actual={actual_nodes}",
    }
