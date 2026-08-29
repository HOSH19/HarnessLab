"""LangSmith Example conversion tests."""

from pathlib import Path

from langsmith.schemas import Example

from harnesslab.experiments.examples import tasks_to_examples
from harnesslab.experiments.tasks import load_tasks


def test_tasks_to_examples_returns_example_objects() -> None:
    """Converted tasks are LangSmith Example schemas with timestamps."""
    root = Path(__file__).resolve().parents[1]
    tasks_dir = root / "examples" / "research_agent" / "tasks"
    examples = tasks_to_examples(load_tasks(tasks_dir)[:1])

    assert len(examples) == 1
    assert isinstance(examples[0], Example)
    assert examples[0].modified_at is not None
    assert "prompt" in (examples[0].inputs or {})
