"""Task fixture loading tests."""

from pathlib import Path

from harnesslab.experiments.tasks import load_tasks


def test_load_tasks_returns_inputs_and_outputs() -> None:
    """Task loader produces LangSmith-compatible records."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "ticket_triage" / "tasks"
    tasks = load_tasks(tasks_dir)
    assert len(tasks) == 10
    assert "inputs" in tasks[0]
    assert "outputs" in tasks[0]
    assert "expected_category" in tasks[0]["outputs"]
