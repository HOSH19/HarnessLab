"""Task fixture loading tests."""

from pathlib import Path

from harnesslab.experiments.tasks import load_tasks


def test_load_tasks_returns_inputs_and_outputs() -> None:
    """Task loader produces LangSmith-compatible records."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "ticket_triage" / "tasks"
    tasks = load_tasks(tasks_dir)
    assert len(tasks) == 13
    assert "inputs" in tasks[0]
    assert "outputs" in tasks[0]
    assert "expected_category" in tasks[0]["outputs"]


def test_load_tasks_includes_stress_fields() -> None:
    """Stress tasks expose flaky_tools, history, and expected_tools."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "ticket_triage" / "tasks"
    tasks = {task["inputs"].get("ticket_id"): task for task in load_tasks(tasks_dir)}

    flaky_task = tasks["T-011"]
    assert flaky_task["inputs"]["flaky_tools"] == {"read_ticket": 1}
    assert flaky_task["outputs"]["stress"] is True
    assert flaky_task["outputs"]["expected_tools"][0] == "read_ticket"

    long_context_task = tasks["T-012"]
    assert len(long_context_task["inputs"]["conversation_history"]) > 8
    assert long_context_task["outputs"]["stress"] is True
