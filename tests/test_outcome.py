"""Task pass evaluator tests."""

from harnesslab.eval.outcome import task_pass


class _FakeRun:
    def __init__(self, outputs):
        self.outputs = outputs


class _FakeExample:
    def __init__(self, outputs):
        self.outputs = outputs


def test_task_pass_full_credit_when_category_and_terms_match() -> None:
    """Perfect classification and reply terms score 1.0."""
    run = _FakeRun(
        {
            "classification": "billing",
            "final_reply": "Refund for order 9912 on account 7788 under annual plan.",
        }
    )
    example = _FakeExample(
        {
            "expected_category": "billing",
            "required_reply_terms": ["7788", "9912", "annual", "refund"],
        }
    )
    result = task_pass(run, example)
    assert result["score"] == 1.0


def test_task_pass_partial_credit_for_some_terms() -> None:
    """Missing reply terms yield partial credit when category is correct."""
    run = _FakeRun(
        {
            "classification": "billing",
            "final_reply": "We can help with your refund request.",
        }
    )
    example = _FakeExample(
        {
            "expected_category": "billing",
            "required_reply_terms": ["7788", "9912", "annual", "refund"],
        }
    )
    result = task_pass(run, example)
    assert result["score"] == 0.62


def test_task_pass_zero_when_category_wrong() -> None:
    """Wrong category caps score at 0.5 even if some terms appear."""
    run = _FakeRun(
        {
            "classification": "technical",
            "final_reply": "refund for annual plan",
        }
    )
    example = _FakeExample(
        {
            "expected_category": "billing",
            "required_reply_terms": ["refund", "annual"],
        }
    )
    result = task_pass(run, example)
    assert result["score"] == 0.5
