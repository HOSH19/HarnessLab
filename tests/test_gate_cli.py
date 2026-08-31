"""Gate CLI output tests."""

from harnesslab.cli.gate_cli import _is_informative_gate_detail


def test_informative_gate_detail_keeps_blocking_evaluators() -> None:
    """Blocking evaluators are always shown even when unchanged."""
    detail = {
        "evaluator": "error_recovery",
        "mean_delta": 0.0,
        "ci_lower": 0.0,
        "ci_upper": 0.0,
    }
    assert _is_informative_gate_detail(detail)


def test_informative_gate_detail_hides_stable_non_blocking() -> None:
    """Stable non-blocking evaluators with zero delta are omitted."""
    detail = {
        "evaluator": "graph_trajectory",
        "mean_delta": 0.0,
        "ci_lower": 0.0,
        "ci_upper": 0.0,
    }
    assert not _is_informative_gate_detail(detail)


def test_informative_gate_detail_shows_nonzero_delta() -> None:
    """Non-blocking evaluators with movement are shown."""
    detail = {
        "evaluator": "efficiency",
        "mean_delta": -0.0017,
        "ci_lower": -0.005,
        "ci_upper": 0.0,
    }
    assert _is_informative_gate_detail(detail)
