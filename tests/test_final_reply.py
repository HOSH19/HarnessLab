"""Tests for final_reply display evaluator."""

from harnesslab.eval.final_reply import final_reply


class _FakeRun:
    def __init__(self, outputs):
        self.outputs = outputs


class _FakeExample:
    outputs = {}


def test_final_reply_evaluator_surfaces_reply_text() -> None:
    """Reply text is exposed as freeform feedback value."""
    result = final_reply(
        _FakeRun({"final_reply": "Refund processed for order 4455."}),
        _FakeExample(),
    )
    assert result["key"] == "reply_text"
    assert result["value"] == "Refund processed for order 4455."
    assert result["score"] == 1.0


def test_final_reply_evaluator_marks_empty_reply() -> None:
    """Missing draft_reply is labeled explicitly."""
    result = final_reply(_FakeRun({"final_reply": ""}), _FakeExample())
    assert result["value"] == "(empty)"
    assert result["score"] == 0.0
