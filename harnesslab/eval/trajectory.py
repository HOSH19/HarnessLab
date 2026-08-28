"""Graph trajectory evaluator for LangSmith experiments.

Scores whether observed graph node steps contain expected nodes
in order. Uses trajectory data attached to run outputs by the runner.
"""

from langsmith.schemas import Example, Run


def _flatten_steps(graph_trajectory: dict) -> list[str]:
    """Flatten nested graph trajectory step lists into one node sequence."""
    steps = graph_trajectory.get("steps", []) if graph_trajectory else []
    flattened: list[str] = []
    for step_group in steps:
        flattened.extend(step_group)
    return [node for node in flattened if node != "__interrupt__"]


def _is_subsequence(expected: list[str], actual: list[str]) -> bool:
    """Return True when expected node names appear in order inside actual."""
    if not expected:
        return True

    index = 0
    for node in actual:
        if node == expected[index]:
            index += 1
            if index == len(expected):
                return True
    return False


def graph_trajectory(run: Run, example: Example) -> dict:
    """Score graph node trajectory against expected node subsequence.

    Args:
        run: LangSmith run containing graph_trajectory in outputs.
        example: Dataset example with expected_nodes reference.

    Returns:
        Dict with score and comment describing node sequence match.
    """
    outputs = run.outputs or {}
    reference = example.outputs or {}
    expected_nodes = reference.get("expected_nodes", [])
    trajectory = outputs.get("graph_trajectory", {})

    actual_nodes = _flatten_steps(trajectory)
    matched = _is_subsequence(expected_nodes, actual_nodes)

    return {
        "key": "graph_trajectory",
        "score": 1.0 if matched else 0.0,
        "comment": f"expected={expected_nodes}, actual={actual_nodes}",
    }
