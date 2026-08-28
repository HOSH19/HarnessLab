"""Tests for run output field helpers."""

from harnesslab.eval.outputs import run_output_field


def test_run_output_field_reads_nested_details() -> None:
    """Evaluators can read fields nested under details."""
    outputs = {
        "output": "billing",
        "classification": "billing",
        "details": {
            "final_reply": "Refund processed.",
            "tool_names": ["classify", "draft_reply"],
        },
    }
    assert run_output_field(outputs, "classification") == "billing"
    assert run_output_field(outputs, "final_reply") == "Refund processed."
    assert run_output_field(outputs, "tool_names") == ["classify", "draft_reply"]
