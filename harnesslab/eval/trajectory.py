"""Graph trajectory evaluator for Langfuse experiments.

Scores whether observed graph node steps contain expected nodes
in order. Uses trajectory data attached to run outputs by the runner.
"""

from harnesslab.eval.outputs import run_output_field
from harnesslab.eval.sequence import subsequence_progress


def _flatten_steps(graph_trajectory: dict) -> list[str]:
    """Flatten nested graph trajectory step lists into one node sequence."""
    steps = graph_trajectory.get("steps", []) if graph_trajectory else []
    flattened: list[str] = []
    for step_group in steps:
        flattened.extend(step_group)
    return [node for node in flattened if node != "__interrupt__"]


def graph_trajectory(run, example) -> dict:
    """Score graph node trajectory against expected node subsequence.

    Args:
        run: Run-like object containing graph_trajectory in outputs.
        example: Dataset example with expected_nodes reference.

    Returns:
        Dict with partial score and comment describing node sequence match.
    """
    outputs = run.outputs or {}
    reference = example.outputs or {}
    expected_nodes = reference.get("expected_nodes", [])
    trajectory = run_output_field(outputs, "graph_trajectory", {})

    actual_nodes = _flatten_steps(trajectory)
    score = subsequence_progress(expected_nodes, actual_nodes)
    matched = score == 1.0

    return {
        "key": "graph_trajectory",
        "score": score,
        "comment": f"matched={matched}, progress={score:.2f}, actual={actual_nodes}",
    }
