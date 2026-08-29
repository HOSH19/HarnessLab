"""Task fixture loading tests."""

from pathlib import Path

from harnesslab.experiments.tasks import load_tasks

CLASSIFY_HINTS = (
    "classify as",
    "false alarm",
    "skip runbook",
    "rollback only",
    "skip kb",
)


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


def test_research_tasks_have_distinct_categories() -> None:
    """Each research task targets a different expected category."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "research_agent" / "tasks"
    tasks = load_tasks(tasks_dir)

    categories = [task["outputs"]["expected_category"] for task in tasks]
    assert categories == ["ml", "systems", "security", "product"]

    for task in tasks:
        prompt = task["inputs"]["prompt"].lower()
        assert not any(hint in prompt for hint in CLASSIFY_HINTS)


def test_incident_tasks_have_distinct_expected_outputs() -> None:
    """Incident tasks have unique categories and neutral prompts."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "incident_manager" / "tasks"
    tasks = {task["inputs"]["ticket_id"]: task for task in load_tasks(tasks_dir)}

    assert tasks["I-101"]["outputs"]["expected_category"] == "infrastructure"
    assert tasks["I-103"]["outputs"]["expected_category"] == "deployment"
    assert tasks["I-104"]["outputs"]["expected_category"] == "security"
    assert tasks["I-106"]["outputs"]["expected_category"] == "data_loss"

    for task in tasks.values():
        prompt = task["inputs"]["prompt"].lower()
        assert "stakeholder update" in prompt
        assert not any(hint in prompt for hint in CLASSIFY_HINTS)
        assert "conversation_history" not in task["inputs"]


def test_incident_manager_stress_fields() -> None:
    """Stress tasks still expose flaky tools where configured."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "incident_manager" / "tasks"
    tasks = {task["inputs"]["ticket_id"]: task for task in load_tasks(tasks_dir)}

    assert tasks["I-103"]["inputs"]["flaky_tools"]["fetch_metrics"] == 2
    assert tasks["I-106"]["outputs"]["max_acceptable_errors"] == 0
