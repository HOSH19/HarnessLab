"""Pareto chart helper tests."""

from harnesslab.report.pareto import pareto_frontier, pareto_points


class _FakeEval:
    def __init__(self, key, score):
        self.key = key
        self.score = score


class _FakeRow:
    def __init__(self, scores: dict[str, float]):
        self.evaluation_results = {"results": [_FakeEval(k, v) for k, v in scores.items()]}


def test_pareto_frontier_prefers_high_pass_low_cost() -> None:
    """Non-dominated arm has best pass-to-cost tradeoff."""
    points = [("retry", 0.9, 0.01), ("minimal", 0.7, 0.005)]
    frontier = pareto_frontier(points)
    assert "retry" in frontier
    assert "minimal" in frontier


def test_pareto_points_reads_compare_rows() -> None:
    """pareto_points averages task_pass and run_cost_usd per arm."""
    comparisons = {
        "retry": [_FakeRow({"task_pass": 1.0, "run_cost_usd": 0.002})],
    }
    points = pareto_points(comparisons)
    assert points == [("retry", 1.0, 0.002)]
