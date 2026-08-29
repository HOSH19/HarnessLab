"""Task fixture loading tests."""

from pathlib import Path

from harnesslab.experiments.tasks import load_tasks


def test_load_tasks_returns_inputs_and_outputs() -> None:
    """Task loader produces Langfuse-compatible records."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "ticket_triage" / "tasks"
    tasks = load_tasks(tasks_dir)
    assert len(tasks) == 9
    assert "inputs" in tasks[0]
    assert "outputs" in tasks[0]
    assert "expected_category" in tasks[0]["outputs"]
    assert tasks[0]["outputs"]["reply_hint"].startswith("include:")


def test_load_tasks_filters_by_ticket_id() -> None:
    """Ticket filter returns a single stress task."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "ticket_triage" / "tasks"
    tasks = load_tasks(tasks_dir, ticket_id="T-018")
    assert len(tasks) == 1
    assert tasks[0]["inputs"]["ticket_id"] == "T-018"


def test_load_tasks_includes_stress_fields() -> None:
    """Stress tasks expose flaky tools, budgets, and adversarial prompts."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "ticket_triage" / "tasks"
    tasks = {task["inputs"].get("ticket_id"): task for task in load_tasks(tasks_dir)}

    tool_budget_task = tasks["T-018"]
    assert tool_budget_task["outputs"]["expected_tools"].count("search_kb") == 2
    assert "check_sla" in tool_budget_task["outputs"]["expected_tools"]
    assert "escalate_ticket" in tool_budget_task["outputs"]["expected_tools"]
    assert tool_budget_task["outputs"]["max_acceptable_errors"] == 0
    assert tool_budget_task["outputs"]["expected_max_steps"] == 10
    assert tool_budget_task["inputs"]["flaky_tools"] == {
        "search_kb": 2,
        "escalate_ticket": 1,
    }

    adversarial_task = tasks["T-019"]
    assert adversarial_task["outputs"]["expected_category"] == "billing"
    assert "skip KB" in adversarial_task["inputs"]["prompt"]
    assert len(adversarial_task["outputs"]["required_reply_terms"]) >= 4
