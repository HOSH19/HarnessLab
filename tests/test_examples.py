"""Local experiment item conversion tests."""

from pathlib import Path

from harnesslab.experiments.examples import tasks_to_local_items
from harnesslab.experiments.tasks import load_tasks


def test_tasks_to_local_items_returns_langfuse_shape() -> None:
    """Converted tasks match Langfuse local experiment item fields."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "ticket_triage" / "tasks"
    items = tasks_to_local_items(load_tasks(tasks_dir)[:1])

    assert len(items) == 1
    assert "input" in items[0]
    assert "expected_output" in items[0]
    assert "prompt" in items[0]["input"]
