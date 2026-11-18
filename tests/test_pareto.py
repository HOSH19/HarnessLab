"""Pareto chart helper tests."""

from harnesslab.eval.cost import estimate_run_cost_usd
from harnesslab.report.pareto import pareto_frontier, pareto_points


class _FakeEval:
    def __init__(self, key, score):
        self.key = key
        self.score = score


class _FakeRow:
    def __init__(self, scores: dict[str, float], run=None):
        self.evaluation_results = {"results": [_FakeEval(k, v) for k, v in scores.items()]}
        self.run = run


class _FakeRun:
    def __init__(self, tokens: int, model: str = "gpt-4.1-nano"):
        self.outputs = {"details": {"total_tokens": tokens, "model": model}}
        self.extra = {}


def test_pareto_frontier_prefers_high_pass_low_cost() -> None:
    """Non-dominated arm has best pass-to-cost tradeoff."""
    points = [("retry", 0.9, 0.01), ("minimal", 0.7, 0.005)]
    frontier = pareto_frontier(points)
    assert "retry" in frontier
    assert "minimal" in frontier


def test_pareto_points_reads_compare_rows() -> None:
    """pareto_points averages task_pass and legacy run_cost_usd feedback when present."""
    comparisons = {
        "retry": [_FakeRow({"task_pass": 1.0, "run_cost_usd": 0.002})],
    }
    points = pareto_points(comparisons)
    assert points == [("retry", 1.0, 0.002)]


def test_pareto_points_estimates_cost_from_run_tokens() -> None:
    """Without published cost feedback, pareto estimates USD from run tokens."""
    run = _FakeRun(tokens=1000)
    comparisons = {
        "retry": [_FakeRow({"task_pass": 1.0}, run=run)],
    }
    points = pareto_points(comparisons)
    assert points == [("retry", 1.0, estimate_run_cost_usd(run))]
