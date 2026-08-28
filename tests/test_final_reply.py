"""Tests for final_reply display evaluator."""

from harnesslab.eval.final_reply import reply_text


class _FakeRun:
    def __init__(self, outputs):
        self.outputs = outputs


class _FakeExample:
    outputs = {}


def test_reply_text_evaluator_surfaces_reply_in_comment() -> None:
    """Reply text is exposed in the evaluator comment, not as a competing output field."""
    result = reply_text(
        _FakeRun({"final_reply": "Refund processed for order 4455."}),
        _FakeExample(),
    )
    assert result["key"] == "reply_text"
    assert result["comment"] == "Refund processed for order 4455."
    assert result["score"] == 1.0
    assert "value" not in result


def test_reply_text_evaluator_marks_empty_reply() -> None:
    """Missing draft_reply is labeled explicitly."""
    result = reply_text(_FakeRun({"final_reply": ""}), _FakeExample())
    assert result["comment"] == "(empty — agent did not call draft_reply)"
    assert result["score"] == 0.0
