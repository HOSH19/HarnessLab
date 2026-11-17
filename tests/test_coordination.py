"""coordination_pass evaluator tests."""

from harnesslab.eval.coordination import coordination_pass


class _FakeRun:
    def __init__(self, outputs):
        self.outputs = outputs


class _FakeExample:
    def __init__(self, outputs):
        self.outputs = outputs


def test_coordination_pass_full_match() -> None:
    """Required stages as subsequence score 1.0."""
    run = _FakeRun(
        {
            "graph_trajectory": {
                "steps": [
                    ["intake"],
                    ["metrics_worker"],
                    ["runbooks_worker"],
                    ["finalize"],
                ]
            }
        }
    )
    example = _FakeExample(
        {"required_stages": ["intake", "metrics_worker", "finalize"]}
    )
    result = coordination_pass(run, example)
    assert result["key"] == "coordination_pass"
    assert result["score"] == 1.0


def test_coordination_pass_skipped_without_stages() -> None:
    """Missing expectations are treated as skipped successes."""
    run = _FakeRun({"graph_trajectory": {"steps": [["agent"], ["tools"]]}})
    example = _FakeExample({})
    result = coordination_pass(run, example)
    assert result["score"] == 1.0
    assert "skipped" in result["comment"]


def test_coordination_pass_partial() -> None:
    """Incomplete stage progress returns a fractional score."""
    run = _FakeRun({"graph_trajectory": {"steps": [["gather"], ["analyze"]]}})
    example = _FakeExample({"required_stages": ["gather", "analyze", "finalize"]})
    result = coordination_pass(run, example)
    assert result["score"] == 2 / 3
