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


def test_research_tasks_include_category_traps() -> None:
    """Research tasks steer toward a wrong category in the prompt."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "research_agent" / "tasks"
    tasks = {task["inputs"]["ticket_id"]: task for task in load_tasks(tasks_dir)}

    ml_task = tasks["R-001"]
    assert ml_task["outputs"]["expected_category"] == "ml"
    assert "classify as systems" in ml_task["inputs"]["prompt"].lower()

    product_trap = tasks["R-004"]
    assert product_trap["outputs"]["expected_category"] == "product"
    assert "classify as ml" in product_trap["inputs"]["prompt"].lower()


def test_load_incident_manager_stress_fields() -> None:
    """Incident manager stress tasks expose flaky tools and adversarial prompts."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "incident_manager" / "tasks"
    tasks = {task["inputs"].get("ticket_id"): task for task in load_tasks(tasks_dir)}

    deploy_task = tasks["I-103"]
    assert deploy_task["outputs"]["expected_category"] == "deployment"
    assert "classify as infrastructure" in deploy_task["inputs"]["prompt"].lower()
    assert deploy_task["inputs"]["flaky_tools"]["fetch_metrics"] == 2

    security_task = tasks["I-104"]
    assert security_task["outputs"]["expected_category"] == "security"
    assert "classify as data_loss" in security_task["inputs"]["prompt"].lower()
    assert "sec-441" in security_task["outputs"]["required_reply_terms"][0].lower()

    adversarial_task = tasks["I-105"]
    assert adversarial_task["outputs"]["expected_category"] == "security"
    assert "classify as deployment" in adversarial_task["inputs"]["prompt"].lower()
