"""Failure category classifier for agent runs.

Maps run errors and outputs to harness-relevant failure fingerprints.
Does not re-execute agents or modify traces.
"""

from langsmith.schemas import Example, Run

from harnesslab.eval.run_metrics import run_latency_seconds

FAILURE_CATEGORIES = (
    "TIMEOUT",
    "TOOL_ERROR",
    "PARSE_ERROR",
    "WRONG_ANSWER",
    "MAX_TURNS",
    "SUCCESS",
)


def _classify_failure(run: Run) -> str:
    """Derive a failure category from a LangSmith run."""
    if run.error:
        error_text = str(run.error).lower()
        if "timeout" in error_text:
            return "TIMEOUT"
        if "tool" in error_text:
            return "TOOL_ERROR"
        return "PARSE_ERROR"

    outputs = run.outputs or {}
    if outputs.get("classification") and outputs.get("final_reply"):
        return "SUCCESS"

    if (run_latency_seconds(run)) > 60:
        return "MAX_TURNS"

    return "WRONG_ANSWER"


def failure_fingerprint(run: Run, example: Example) -> dict:
    """Score run outcome by failure category fingerprint.

    Args:
        run: LangSmith run to classify.
        example: Dataset example (unused, required by LangSmith API).

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
