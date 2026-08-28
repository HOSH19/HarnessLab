"""Evaluator adapter tests."""

from harnesslab.eval.adapter import adapt_evaluator
from harnesslab.eval.outcome import task_pass


def test_adapt_evaluator_wraps_legacy_scorer() -> None:
    """Legacy scorers return Langfuse Evaluation objects."""
    evaluator = adapt_evaluator(task_pass)
    result = evaluator(
        input={"prompt": "Triage ticket T-015", "ticket_id": "T-015"},
        output={"classification": "technical", "final_reply": "ssl certificate expired"},
        expected_output={
            "expected_category": "technical",
            "required_reply_terms": ["ssl", "certificate"],
        },
        metadata=None,
    )
    assert result.name == "task_pass"
    assert result.value == 1.0
