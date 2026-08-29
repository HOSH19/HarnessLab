"""Shared helpers for parsing Langfuse experiment result rows."""

from typing import Any

SUMMARY_KEYS = [
    "task_pass",
    "graph_trajectory",
    "tool_sequence",
    "error_recovery",
    "step_count",
    "efficiency",
    "failure_fingerprint",
]

DETAIL_KEYS = [
    "task_pass",
    "tool_sequence",
    "error_recovery",
    "step_count",
    "efficiency",
]


def row_value(row: Any, key: str, default: Any = None) -> Any:
    """Read a field from a result row object or dict."""
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


def evaluation_results(row: Any) -> list:
    """Return evaluator result items from an experiment row."""
    feedback = row_value(row, "evaluation_results", {}) or {}
    return getattr(feedback, "results", None) or feedback.get("results", []) or []


def score_for_key(row: Any, key: str) -> float | None:
    """Return one evaluator score from a result row when present."""
    for result in evaluation_results(row):
        result_key = getattr(result, "key", None) or result.get("key")
        if result_key != key:
            continue
        result_score = getattr(result, "score", None)
        if result_score is None and isinstance(result, dict):
            result_score = result.get("score")
        if result_score is not None:
            return float(result_score)
    return None


def comment_for_key(row: Any, key: str) -> str:
    """Return one evaluator comment from a result row when present."""
    for result in evaluation_results(row):
        result_key = getattr(result, "key", None) or result.get("key")
        if result_key != key:
            continue
        comment = getattr(result, "comment", None)
        if comment is None and isinstance(result, dict):
            comment = result.get("comment")
        return str(comment or "")
    return ""


def avg_score(results: list, key: str) -> float:
    """Compute average evaluator score from experiment result rows."""
    scores = [score_for_key(row, key) for row in results]
    scores = [score for score in scores if score is not None]
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def task_label(row: Any) -> str:
    """Derive a stable task label from an experiment result row."""
    example = row_value(row, "example", {}) or {}
    inputs = getattr(example, "inputs", None) or example.get("inputs", {}) or {}
    ticket_id = inputs.get("ticket_id")
    if ticket_id:
        return str(ticket_id)
    prompt = inputs.get("prompt", "")
    if prompt:
        return str(prompt)[:40]
    return "unknown"


def harness_summary(results: list) -> dict[str, float]:
    """Aggregate average evaluator scores for one harness."""
    return {key: avg_score(results, key) for key in SUMMARY_KEYS}
