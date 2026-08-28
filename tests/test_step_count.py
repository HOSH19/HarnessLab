"""Step count evaluator tests."""

from harnesslab.eval.step_count import step_count


class _FakeRun:
    def __init__(self, child_runs=None):
        self.child_runs = child_runs or []


class _FakeExample:
    def __init__(self, outputs):
        self.outputs = outputs


def test_step_count_full_score_within_budget() -> None:
    """Runs at or below expected_max_steps score 1.0."""
    run = _FakeRun(child_runs=[object()] * 8)
    example = _FakeExample({"expected_max_steps": 12})
    result = step_count(run, example)
    assert result["score"] == 1.0


def test_step_count_scales_down_when_over_budget() -> None:
    """Runs over the step budget receive a proportional score."""
    run = _FakeRun(child_runs=[object()] * 16)
    example = _FakeExample({"expected_max_steps": 8})
    result = step_count(run, example)
    assert result["score"] == 0.5


def test_step_count_defaults_expected_max_steps() -> None:
    """Missing expected_max_steps defaults to 12 steps."""
    run = _FakeRun(child_runs=[object()] * 10)
    example = _FakeExample({})
    result = step_count(run, example)
    assert result["score"] == 1.0
    assert "expected_max=12" in result["comment"]
