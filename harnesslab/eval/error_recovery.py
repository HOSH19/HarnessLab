"""Error recovery evaluator for agent runs."""

from harnesslab.eval.types import EvalExample, EvalRun


def error_recovery(run: EvalRun, example: EvalExample) -> dict:
    """Score whether the agent stayed within acceptable error limits."""
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
