"""Error recovery evaluator for agent runs.

Scores runs based on error_count versus per-task tolerance.
Does not re-execute agents or inspect trace logs.
"""

from langsmith.schemas import Example, Run


def error_recovery(run: Run, example: Example) -> dict:
    """Score whether the agent stayed within acceptable error limits.

    Args:
        run: LangSmith run with error_count in outputs.
        example: Dataset example with optional max_acceptable_errors.

    Returns:
        Dict with normalized score and error budget comment.
    """
    outputs = run.outputs or {}
    reference = example.outputs or {}
    error_count = int(outputs.get("error_count", 0))
    max_acceptable = int(reference.get("max_acceptable_errors", 0))

    if error_count <= max_acceptable:
        score = 1.0
    else:
        excess = error_count - max_acceptable
        score = max(0.0, 1.0 - 0.25 * excess)

    return {
        "key": "error_recovery",
        "score": score,
        "comment": f"error_count={error_count}, max_acceptable={max_acceptable}",
    }
