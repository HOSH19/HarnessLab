"""Error recovery evaluator tests."""

from harnesslab.eval.error_recovery import error_recovery


class _FakeRun:
    def __init__(self, outputs):
        self.outputs = outputs


class _FakeExample:
    def __init__(self, outputs):
        self.outputs = outputs


def test_error_recovery_passes_within_budget() -> None:
    """Runs within the error budget score 1.0."""
    run = _FakeRun({"error_count": 1})
    example = _FakeExample({"max_acceptable_errors": 2})
    result = error_recovery(run, example)
    assert result["score"] == 1.0


def test_error_recovery_defaults_to_zero_tolerance() -> None:
    """Missing max_acceptable_errors defaults to zero errors allowed."""
    run = _FakeRun({"error_count": 1})
    example = _FakeExample({})
    result = error_recovery(run, example)
    assert result["score"] == 0.75


def test_error_recovery_penalizes_excess_errors() -> None:
    """Each excess error reduces the score by 0.25."""
    run = _FakeRun({"error_count": 4})
    example = _FakeExample({"max_acceptable_errors": 1})
    result = error_recovery(run, example)
    assert result["score"] == 0.25
