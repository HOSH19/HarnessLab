"""Generate HTML comparison reports from experiment results.

Formats harness A/B outcomes as tables. Does not fetch from LangSmith
API in v1; accepts in-memory experiment result lists.
"""

import re
from pathlib import Path
from typing import Any

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


def _pareto_frontier(points: list[tuple[str, float, float]]) -> set[str]:
    """Return arm names on the Pareto frontier (max task_pass, min cost)."""
    frontier: set[str] = set()
    for name, pass_score, cost in points:
        dominated = False
        for other_name, other_pass, other_cost in points:
            if other_name == name:
                continue
            if other_pass >= pass_score and other_cost <= cost and (
                other_pass > pass_score or other_cost < cost
            ):
                dominated = True
                break
        if not dominated:
            frontier.add(name)
    return frontier


def _render_pareto_svg(points: list[tuple[str, float, float]], frontier: set[str]) -> str:
    """Render a simple SVG scatter for task_pass vs run_cost_usd."""
    if not points:
        return ""

    width, height, pad = 420, 260, 40
    max_cost = max(cost for _, _, cost in points) or 1e-6
    max_pass = max(pass_score for _, pass_score, _ in points) or 1.0

    circles = []
    for name, pass_score, cost in points:
        x = pad + (cost / max_cost) * (width - 2 * pad)
        y = height - pad - (pass_score / max_pass) * (height - 2 * pad)
        color = "#2a9d8f" if name in frontier else "#457b9d"
        circles.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{color}" />'
            f'<text x="{x + 10:.1f}" y="{y + 4:.1f}" font-size="12">{name}</text>'
        )

    return f"""
  <h2>Cost vs accuracy (Pareto)</h2>
  <p>Green dots are non-dominated arms (high task_pass, low run_cost_usd).</p>
  <svg width="{width}" height="{height}" style="border:1px solid #ccc">
    <line x1="{pad}" y1="{height - pad}" x2="{width - pad}" y2="{height - pad}" stroke="#333" />
    <line x1="{pad}" y1="{pad}" x2="{pad}" y2="{height - pad}" stroke="#333" />
    <text x="{width // 2}" y="{height - 8}" font-size="12" text-anchor="middle">run_cost_usd (avg)</text>
    <text x="12" y="{height // 2}" font-size="12" transform="rotate(-90 12,{height // 2})">task_pass (avg)</text>
    {''.join(circles)}
  </svg>"""


def render_comparison_html(
    comparisons: dict[str, list[dict]],
    *,
    dimension: str = "Harness",
) -> str:
    """Render comparison results as an HTML table.

    Args:
        comparisons: Mapping of arm name (harness or model) to experiment result rows.
        dimension: Column label for the comparison arm ("Harness" or "Model").

    Returns:
        HTML string with per-arm score summary and per-task detail.
    """
    summary_headers = [dimension, *SUMMARY_KEYS]
    summary_rows = []
    for arm_name, results in comparisons.items():
        summary_rows.append(
            "<tr>"
            f"<td>{arm_name}</td>"
            + "".join(f"<td>{avg_score(results, key):.2f}</td>" for key in SUMMARY_KEYS)
            + "</tr>"
        )

    detail_headers = [
        dimension,
        "Task",
        *DETAIL_KEYS,
        "latency_ms",
        "tokens",
        "steps",
    ]
    detail_rows = []
    for arm_name, results in comparisons.items():
        for row in results:
            detail_rows.append(
                "<tr>"
                f"<td>{arm_name}</td>"
                f"<td>{task_label(row)}</td>"
                f"{_detail_metric_cells(row)}"
                "</tr>"
            )

    title = f"HarnessLab {dimension} Comparison"
    summary_body = "\n".join(summary_rows)
    detail_body = "\n".join(detail_rows)

    pareto_points = [
        (arm_name, avg_score(results, "task_pass"), avg_score(results, "run_cost_usd"))
        for arm_name, results in comparisons.items()
    ]
    frontier = _pareto_frontier(pareto_points)
    pareto_svg = _render_pareto_svg(pareto_points, frontier)

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
    """Write comparison HTML report to disk.

    Args:
        comparisons: Mapping of arm name to experiment result rows.
        output_path: Destination file path.
        dimension: Column label for the comparison arm.

    Returns:
        Resolved output path.
    """
    html = render_comparison_html(comparisons, dimension=dimension)
    output_path.write_text(html)
    return output_path.resolve()
