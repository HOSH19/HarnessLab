"""Runner and dataset output shape tests."""

from pathlib import Path

from harnesslab.eval.outputs import run_output_field
from harnesslab.experiments.tasks import load_tasks


def test_dataset_outputs_include_output_for_langsmith_preview() -> None:
    """Reference outputs expose output=classification for LangSmith table columns."""
    root = Path(__file__).resolve().parents[1]
    tasks = load_tasks(root / "examples" / "incident_manager" / "tasks", ticket_id="I-101")

    outputs = tasks[0]["outputs"]
    assert outputs["classification"] == "infrastructure"
    assert outputs["output"] == "infrastructure"


def test_run_output_field_reads_nested_reply_and_trajectory() -> None:
    """Evaluators read final_reply and graph_trajectory from details."""
    outputs = {
        "output": "infrastructure",
        "classification": "infrastructure",
        "error_count": 0,
        "details": {
            "final_reply": "Pool exhaustion on payments-api.",
            "graph_trajectory": {"steps": [["agent"], ["tools"]], "results": [], "inputs": []},
            "total_tokens": 100,
            "model": "gpt-4.1-nano",
        },
    }
    assert run_output_field(outputs, "final_reply") == "Pool exhaustion on payments-api."
    assert run_output_field(outputs, "graph_trajectory")["steps"] == [["agent"], ["tools"]]
    assert run_output_field(outputs, "total_tokens") == 100
    assert run_output_field(outputs, "model") == "gpt-4.1-nano"
    assert "final_reply" not in outputs
    assert "model" not in outputs
