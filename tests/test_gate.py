"""Harness regression gate tests."""

from harnesslab.gate.check import check_regression
from harnesslab.gate.significance import bootstrap_mean_delta


class _FakeEval:
    def __init__(self, key, score):
        self.key = key
        self.score = score


class _FakeExample:
    inputs = {"ticket_id": "I-101"}


class _FakeRow:
    def __init__(self, scores: dict[str, float]):
        self.example = _FakeExample()
        self.evaluation_results = {"results": [_FakeEval(k, v) for k, v in scores.items()]}


def test_bootstrap_mean_delta_positive_when_current_higher() -> None:
    """Bootstrap delta is positive when current scores exceed baseline."""
    mean_delta, lower, upper = bootstrap_mean_delta([0.5, 0.5], [0.9, 0.9], samples=200, seed=1)
    assert mean_delta > 0
    assert lower > 0


def test_gate_passes_when_scores_hold() -> None:
    """Gate passes when current scores match the baseline."""
    baseline = {
        "arms": {
            "retry": {
                "task_pass": 1.0,
                "error_recovery": 1.0,
                "per_task": {"I-101": {"task_pass": 1.0, "error_recovery": 1.0}},
            }
        }
    }
    comparisons = {
        "retry": [_FakeRow({"task_pass": 1.0, "error_recovery": 1.0})],
    }
    result = check_regression(
        baseline=baseline,
        comparisons=comparisons,
        summary_keys=["task_pass", "error_recovery"],
    )
    assert result.passed


def test_gate_fails_on_large_regression() -> None:
    """Gate fails when task_pass drops materially below baseline."""
    baseline = {
        "arms": {
            "retry": {
                "task_pass": 1.0,
                "error_recovery": 1.0,
                "per_task": {"I-101": {"task_pass": 1.0, "error_recovery": 1.0}},
            }
        }
    }
    comparisons = {
        "retry": [_FakeRow({"task_pass": 0.0, "error_recovery": 1.0})],
    }
    result = check_regression(
        baseline=baseline,
        comparisons=comparisons,
        summary_keys=["task_pass", "error_recovery"],
        max_regression=0.05,
    )
    assert not result.passed
    assert result.failures
