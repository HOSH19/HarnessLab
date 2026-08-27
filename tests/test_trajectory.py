"""Graph trajectory evaluator tests."""

from harnesslab.eval.trajectory import _flatten_steps, _is_subsequence, graph_trajectory


class _FakeRun:
    def __init__(self, outputs):
        self.outputs = outputs


class _FakeExample:
    def __init__(self, outputs):
        self.outputs = outputs


def test_is_subsequence_matches_in_order() -> None:
    """Expected nodes must appear in order within actual nodes."""
    assert _is_subsequence(["agent", "tools"], ["trim_context", "agent", "tools", "agent"]) is True
    assert _is_subsequence(["tools", "agent"], ["agent", "tools"]) is False


def test_graph_trajectory_scores_expected_nodes() -> None:
    """Graph trajectory evaluator returns pass when nodes are present."""
    run = _FakeRun({"graph_trajectory": {"steps": [["agent"], ["tools"]]}})
    example = _FakeExample({"expected_nodes": ["agent", "tools"]})
    result = graph_trajectory(run, example)
    assert result["score"] == 1.0


def test_flatten_steps_skips_interrupt_marker() -> None:
    """Flattened trajectory ignores interrupt markers."""
    flattened = _flatten_steps({"steps": [["agent", "__interrupt__"], ["tools"]]})
    assert flattened == ["agent", "tools"]
