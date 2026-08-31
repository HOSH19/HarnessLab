"""Pareto frontier helpers for harness cost vs accuracy reports."""

from harnesslab.report.results import avg_score


def pareto_points(comparisons: dict[str, list]) -> list[tuple[str, float, float]]:
    """Build (arm, task_pass, run_cost_usd) tuples for each compare arm."""
    return [
        (arm_name, avg_score(results, "task_pass"), avg_score(results, "run_cost_usd"))
        for arm_name, results in comparisons.items()
    ]


def pareto_frontier(points: list[tuple[str, float, float]]) -> set[str]:
    """Return arm names that are not dominated on pass rate and cost."""
    frontier: set[str] = set()
    for name, pass_score, cost in points:
        if not _is_dominated(name, pass_score, cost, points):
            frontier.add(name)
    return frontier


def _is_dominated(
    name: str,
    pass_score: float,
    cost: float,
    points: list[tuple[str, float, float]],
) -> bool:
    """Return True when another arm is strictly better on pass and cost."""
    for other_name, other_pass, other_cost in points:
        if other_name == name:
            continue
        if other_pass >= pass_score and other_cost <= cost:
            if other_pass > pass_score or other_cost < cost:
                return True
    return False


def render_pareto_svg(points: list[tuple[str, float, float]], frontier: set[str]) -> str:
    """Render an inline SVG scatter of task_pass vs run_cost_usd."""
    if not points:
        return ""

    width, height, pad = 420, 260, 40
    max_cost = max(cost for _, _, cost in points) or 1e-6
    max_pass = max(pass_score for _, pass_score, _ in points) or 1.0
    circles = [_svg_point(name, pass_score, cost, frontier, width, height, pad, max_pass, max_cost)
               for name, pass_score, cost in points]

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


def _svg_point(
    name: str,
    pass_score: float,
    cost: float,
    frontier: set[str],
    width: int,
    height: int,
    pad: int,
    max_pass: float,
    max_cost: float,
) -> str:
    """Render one labeled scatter point."""
    x = pad + (cost / max_cost) * (width - 2 * pad)
    y = height - pad - (pass_score / max_pass) * (height - 2 * pad)
    color = "#2a9d8f" if name in frontier else "#457b9d"
    return (
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{color}" />'
        f'<text x="{x + 10:.1f}" y="{y + 4:.1f}" font-size="12">{name}</text>'
    )
