"""Generate HTML comparison reports from experiment results.

Formats harness A/B outcomes as tables. Does not fetch from LangSmith
API in v1; accepts in-memory experiment result lists.
"""

import re
from pathlib import Path
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


def _row_value(row: Any, key: str, default: Any = None) -> Any:
    """Read a field from a result row object or dict."""
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


def _evaluation_results(row: Any) -> list:
    """Return evaluator result items from an experiment row."""
    feedback = _row_value(row, "evaluation_results", {}) or {}
    return getattr(feedback, "results", None) or feedback.get("results", []) or []


def _score_for_key(row: Any, key: str) -> float | None:
    """Return one evaluator score from a result row when present."""
    for result in _evaluation_results(row):
        result_key = getattr(result, "key", None) or result.get("key")
        if result_key != key:
            continue
        result_score = getattr(result, "score", None)
        if result_score is None and isinstance(result, dict):
            result_score = result.get("score")
        if result_score is not None:
            return float(result_score)
    return None


def _comment_for_key(row: Any, key: str) -> str:
    """Return one evaluator comment from a result row when present."""
    for result in _evaluation_results(row):
        result_key = getattr(result, "key", None) or result.get("key")
        if result_key != key:
            continue
        comment = getattr(result, "comment", None)
        if comment is None and isinstance(result, dict):
            comment = result.get("comment")
        return str(comment or "")
    return ""


def _avg_score(results: list, key: str) -> float:
    """Compute average evaluator score from experiment result rows."""
    scores = [_score_for_key(row, key) for row in results]
    scores = [score for score in scores if score is not None]
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def _task_label(row: Any) -> str:
    """Derive a stable task label from an experiment result row."""
    example = _row_value(row, "example", {}) or {}
    inputs = getattr(example, "inputs", None) or example.get("inputs", {}) or {}
    ticket_id = inputs.get("ticket_id")
    if ticket_id:
        return str(ticket_id)
    prompt = inputs.get("prompt", "")
    if prompt:
        return str(prompt)[:40]
    return "unknown"


def _parse_efficiency_comment(comment: str) -> dict[str, str]:
    """Parse latency, token, and step fields from efficiency comments."""
    parsed: dict[str, str] = {}
    for field in ("latency_ms", "tokens", "steps"):
        match = re.search(rf"{field}=([^,\s]+)", comment)
        if match:
            parsed[field] = match.group(1)
    return parsed


def _detail_metric_cells(row: Any) -> str:
    """Render per-task metric cells for the detail table."""
    cells: list[str] = []
    for key in DETAIL_KEYS:
        score = _score_for_key(row, key)
        score_text = f"{score:.2f}" if score is not None else "-"
        cells.append(f"<td>{score_text}</td>")

    efficiency = _parse_efficiency_comment(_comment_for_key(row, "efficiency"))
    cells.append(f"<td>{efficiency.get('latency_ms', '-')}</td>")
    cells.append(f"<td>{efficiency.get('tokens', '-')}</td>")
    cells.append(f"<td>{efficiency.get('steps', '-')}</td>")
    return "".join(cells)


def render_comparison_html(comparisons: dict[str, list[dict]]) -> str:
    """Render harness comparison results as an HTML table.

    Args:
        comparisons: Mapping of harness name to experiment result rows.

    Returns:
        HTML string with per-harness score summary and per-task detail.
    """
    summary_headers = ["Harness", *SUMMARY_KEYS]
    summary_rows = []
    for harness_name, results in comparisons.items():
        summary_rows.append(
            "<tr>"
            f"<td>{harness_name}</td>"
            + "".join(f"<td>{_avg_score(results, key):.2f}</td>" for key in SUMMARY_KEYS)
            + "</tr>"
        )

    detail_headers = [
        "Harness",
        "Task",
        *DETAIL_KEYS,
        "latency_ms",
        "tokens",
        "steps",
    ]
    detail_rows = []
    for harness_name, results in comparisons.items():
        for row in results:
            detail_rows.append(
                "<tr>"
                f"<td>{harness_name}</td>"
                f"<td>{_task_label(row)}</td>"
                f"{_detail_metric_cells(row)}"
                "</tr>"
            )

    summary_body = "\n".join(summary_rows)
    detail_body = "\n".join(detail_rows)
    return f"""<!DOCTYPE html>
<html>
<head><title>HarnessLab Comparison</title></head>
<body>
  <h1>Harness A/B Comparison</h1>
  <h2>Summary</h2>
  <table border="1" cellpadding="8">
    <tr>{''.join(f'<th>{header}</th>' for header in summary_headers)}</tr>
    {summary_body}
  </table>
  <h2>Per-task breakdown</h2>
  <table border="1" cellpadding="8">
    <tr>{''.join(f'<th>{header}</th>' for header in detail_headers)}</tr>
    {detail_body}
  </table>
</body>
</html>"""


def write_report(comparisons: dict[str, list[dict]], output_path: Path) -> Path:
    """Write comparison HTML report to disk.

    Args:
        comparisons: Mapping of harness name to experiment result rows.
        output_path: Destination file path.

    Returns:
        Resolved output path.
    """
    html = render_comparison_html(comparisons)
    output_path.write_text(html)
    return output_path.resolve()
