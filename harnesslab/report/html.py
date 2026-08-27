"""Generate HTML comparison reports from experiment results.

Formats harness A/B outcomes as tables. Does not fetch from LangSmith
API in v1; accepts in-memory experiment result lists.
"""

from pathlib import Path
from typing import Any


def _avg_score(results: list, key: str) -> float:
    """Compute average evaluator score from experiment result rows."""
    scores = []
    for row in results:
        feedback = getattr(row, "evaluation_results", None) or row.get("evaluation_results", {})
        result_items = getattr(feedback, "results", None) or feedback.get("results", [])
        for result in result_items:
            result_key = getattr(result, "key", None) or result.get("key")
            result_score = getattr(result, "score", None)
            if result_score is None and isinstance(result, dict):
                result_score = result.get("score")
            if result_key == key and result_score is not None:
                scores.append(float(result_score))
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def render_comparison_html(comparisons: dict[str, list[dict]]) -> str:
    """Render harness comparison results as an HTML table.

    Args:
        comparisons: Mapping of harness name to experiment result rows.

    Returns:
        HTML string with per-harness score summary.
    """
    headers = ["Harness", "task_pass", "graph_trajectory", "efficiency", "failure_fingerprint"]
    rows = []
    for harness_name, results in comparisons.items():
        rows.append(
            "<tr>"
            f"<td>{harness_name}</td>"
            f"<td>{_avg_score(results, 'task_pass'):.2f}</td>"
            f"<td>{_avg_score(results, 'graph_trajectory'):.2f}</td>"
            f"<td>{_avg_score(results, 'efficiency'):.2f}</td>"
            f"<td>{_avg_score(results, 'failure_fingerprint'):.2f}</td>"
            "</tr>"
        )

    body = "\n".join(rows)
    return f"""<!DOCTYPE html>
<html>
<head><title>HarnessLab Comparison</title></head>
<body>
  <h1>Harness A/B Comparison</h1>
  <table border="1" cellpadding="8">
    <tr>{''.join(f'<th>{h}</th>' for h in headers)}</tr>
    {body}
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
