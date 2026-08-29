"""Langfuse local experiment item conversion tests."""

from pathlib import Path

from harnesslab.experiments.examples import tasks_to_examples
from harnesslab.experiments.tasks import load_tasks


def test_tasks_to_examples_returns_local_items() -> None:
    """Converted tasks are Langfuse local experiment items."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "ticket_triage" / "tasks"
    examples = tasks_to_examples(load_tasks(tasks_dir)[:1])

    assert len(examples) == 1
    assert "input" in examples[0]
    assert "expected_output" in examples[0]
    assert "prompt" in examples[0]["input"]
