"""Task fixture loading tests."""

from pathlib import Path

from harnesslab.experiments.tasks import load_tasks


def test_load_research_tasks_returns_inputs_and_outputs() -> None:
    """Research task loader produces LangSmith-compatible records."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "research_agent" / "tasks"
    tasks = load_tasks(tasks_dir)
    assert len(tasks) == 4
    assert "inputs" in tasks[0]
    assert "outputs" in tasks[0]
    assert "expected_category" in tasks[0]["outputs"]
    assert tasks[0]["outputs"]["reply_hint"].startswith("include:")


def test_load_tasks_filters_by_ticket_id() -> None:
    """Ticket filter returns a single task."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "research_agent" / "tasks"
    tasks = load_tasks(tasks_dir, ticket_id="R-002")
    assert len(tasks) == 1
    assert tasks[0]["inputs"]["ticket_id"] == "R-002"


def test_load_incident_manager_stress_fields() -> None:
    """Incident manager stress tasks expose flaky tools and adversarial prompts."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "incident_manager" / "tasks"
    tasks = {task["inputs"].get("ticket_id"): task for task in load_tasks(tasks_dir)}

    deploy_task = tasks["I-103"]
    assert "correlate_timeline" in deploy_task["outputs"]["expected_tools"]
    assert deploy_task["inputs"]["flaky_tools"]["fetch_metrics"] == 2

    adversarial_task = tasks["I-105"]
    assert adversarial_task["outputs"]["expected_category"] == "security"
    assert "skip runbook" in adversarial_task["inputs"]["prompt"].lower()
