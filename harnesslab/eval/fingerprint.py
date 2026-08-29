"""Failure category classifier for agent runs.

Maps run errors and outputs to harness-relevant failure fingerprints.
Does not re-execute agents or modify traces.
"""
from harnesslab.eval.outputs import run_output_field
from harnesslab.eval.run_metrics import run_latency_seconds

FAILURE_CATEGORIES = (
    "TIMEOUT",
    "TOOL_ERROR",
    "PARSE_ERROR",
    "WRONG_ANSWER",
    "MAX_TURNS",
    "SUCCESS",
)


def _classify_failure(run) -> str:
    """Derive a failure category from a run-like object."""
    if run.error:
        error_text = str(run.error).lower()
        if "timeout" in error_text:
            return "TIMEOUT"
        if "tool" in error_text:
            return "TOOL_ERROR"
        return "PARSE_ERROR"

    outputs = run.outputs or {}
    if run_output_field(outputs, "classification") and run_output_field(outputs, "final_reply"):
        return "SUCCESS"

    if (run_latency_seconds(run)) > 60:
        return "MAX_TURNS"

    return "WRONG_ANSWER"


def failure_fingerprint(run, example) -> dict:
    """Score run outcome by failure category fingerprint.

    Args:
        run: Run-like object to classify.
        example: Dataset example (unused, required by evaluator API).

    Returns:
        Dict with score 1.0 for SUCCESS else 0.0 and category comment.
    """
    _ = example
    category = _classify_failure(run)
    return {
        "key": "failure_fingerprint",
        "score": 1.0 if category == "SUCCESS" else 0.0,
        "comment": category,
    }
