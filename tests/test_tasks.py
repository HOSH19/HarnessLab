"""Task fixture loading tests."""

from pathlib import Path

from harnesslab.experiments.tasks import load_tasks


def test_load_tasks_returns_inputs_and_outputs() -> None:
    """Task loader produces LangSmith-compatible records."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "ticket_triage" / "tasks"
    tasks = load_tasks(tasks_dir)
    assert len(tasks) == 6
    assert "inputs" in tasks[0]
    assert "outputs" in tasks[0]
    assert "expected_category" in tasks[0]["outputs"]


def test_load_tasks_filters_by_ticket_id() -> None:
    """Ticket filter returns a single stress task."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "ticket_triage" / "tasks"
    tasks = load_tasks(tasks_dir, ticket_id="T-011")
    assert len(tasks) == 1
    assert tasks[0]["inputs"]["ticket_id"] == "T-011"


def test_load_tasks_includes_stress_fields() -> None:
    """Stress tasks expose flaky_tools, history, and expected_tools."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "ticket_triage" / "tasks"
    tasks = {task["inputs"].get("ticket_id"): task for task in load_tasks(tasks_dir)}

    flaky_task = tasks["T-011"]
    assert flaky_task["inputs"]["flaky_tools"] == {"read_ticket": 2}
    assert flaky_task["outputs"]["stress"] is True
    assert flaky_task["outputs"]["expected_tools"][0] == "read_ticket"

    long_context_task = tasks["T-012"]
    assert len(long_context_task["inputs"]["conversation_history"]) >= 24
    assert long_context_task["outputs"]["stress"] is True

    multi_kb_task = tasks["T-014"]
    assert multi_kb_task["outputs"]["expected_tools"].count("search_kb") == 2

    flaky_search_task = tasks["T-015"]
    assert flaky_search_task["inputs"]["flaky_tools"] == {"search_kb": 2}
    assert flaky_search_task["outputs"]["max_acceptable_errors"] == 2

    low_turns_task = tasks["T-016"]
    assert "check_sla" in low_turns_task["outputs"]["expected_tools"]
    assert "escalate_ticket" in low_turns_task["outputs"]["expected_tools"]
    assert low_turns_task["outputs"]["max_acceptable_errors"] == 0
