"""HTML comparison reports for harness A/B experiment results."""

import re
from pathlib import Path
from typing import Any

from harnesslab.report.pareto import pareto_frontier, pareto_points, render_pareto_svg
from harnesslab.report.results import (
    DETAIL_KEYS,
    SUMMARY_KEYS,
    avg_score,
    comment_for_key,
    score_for_key,
    task_label,
)


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
        score = score_for_key(row, key)
        score_text = f"{score:.2f}" if score is not None else "-"
        cells.append(f"<td>{score_text}</td>")

    efficiency = _parse_efficiency_comment(comment_for_key(row, "efficiency"))
    cells.append(f"<td>{efficiency.get('latency_ms', '-')}</td>")
    cells.append(f"<td>{efficiency.get('tokens', '-')}</td>")
    cells.append(f"<td>{efficiency.get('steps', '-')}</td>")
    return "".join(cells)


def _summary_table(comparisons: dict[str, list], dimension: str) -> tuple[list[str], str]:
    """Build summary table headers and HTML body rows."""
    headers = [dimension, *SUMMARY_KEYS]
    rows = []
    for arm_name, results in comparisons.items():
        cells = "".join(f"<td>{avg_score(results, key):.2f}</td>" for key in SUMMARY_KEYS)
        rows.append(f"<tr><td>{arm_name}</td>{cells}</tr>")
    return headers, "\n".join(rows)


def _detail_table(comparisons: dict[str, list], dimension: str) -> tuple[list[str], str]:
    """Build per-task detail table headers and HTML body rows."""
    headers = [dimension, "Task", *DETAIL_KEYS, "latency_ms", "tokens", "steps"]
    rows = []
    for arm_name, results in comparisons.items():
        for row in results:
            rows.append(
                f"<tr><td>{arm_name}</td><td>{task_label(row)}</td>{_detail_metric_cells(row)}</tr>"
            )
    return headers, "\n".join(rows)


def render_comparison_html(
    comparisons: dict[str, list[dict]],
    *,
    dimension: str = "Harness",
) -> str:
    """Render comparison results as HTML tables plus a Pareto chart."""
    summary_headers, summary_body = _summary_table(comparisons, dimension)
    detail_headers, detail_body = _detail_table(comparisons, dimension)
    points = pareto_points(comparisons)
    pareto_svg = render_pareto_svg(points, pareto_frontier(points))
    title = f"HarnessLab {dimension} Comparison"

    return f"""<!DOCTYPE html>
<html>
<head><title>{title}</title></head>
<body>
  <h1>{title}</h1>
  {pareto_svg}
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


def write_report(
    comparisons: dict[str, list[dict]],
    output_path: Path,
    *,
    dimension: str = "Harness",
) -> Path:
    """Write comparison HTML report to disk and return the resolved path."""
    output_path.write_text(render_comparison_html(comparisons, dimension=dimension))
    return output_path.resolve()
