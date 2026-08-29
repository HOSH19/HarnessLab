"""Runner and dataset output shape tests."""

from pathlib import Path

from harnesslab.experiments.tasks import load_tasks


def test_dataset_outputs_include_output_for_langsmith_preview() -> None:
    """Reference outputs expose output=classification for LangSmith table columns."""
    root = Path(__file__).resolve().parents[1]
    tasks = load_tasks(root / "examples" / "incident_manager" / "tasks", ticket_id="I-101")

    outputs = tasks[0]["outputs"]
    assert outputs["classification"] == "infrastructure"
    assert outputs["output"] == "infrastructure"
