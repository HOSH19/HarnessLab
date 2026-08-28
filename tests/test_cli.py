"""CLI helper tests."""

from harnesslab.cli.main import DEFAULT_COMPARE_HARNESSES, DEFAULT_TASK_LIMIT, _resolve_task_limit


def test_default_task_limit_is_two() -> None:
    """Compare runs default to two stress tasks."""
    assert _resolve_task_limit(None, None) == DEFAULT_TASK_LIMIT
    assert DEFAULT_TASK_LIMIT == 2


def test_single_task_filter_ignores_default_limit() -> None:
    """A --task filter runs one ticket without applying the task cap."""
    assert _resolve_task_limit(None, "T-011") is None
    assert _resolve_task_limit(6, "T-011") == 6


def test_explicit_tasks_override_default() -> None:
    """--tasks overrides the default cap when no ticket filter is set."""
    assert _resolve_task_limit(6, None) == 6


def test_default_compare_harnesses_are_minimal_and_retry() -> None:
    """Harness compare defaults to minimal and retry arms."""
    assert DEFAULT_COMPARE_HARNESSES == "minimal,retry"


def test_resolve_dataset_name_uses_explicit_value() -> None:
    """--dataset overrides the example-derived default."""
    from pathlib import Path

    from harnesslab.cli.main import _default_dataset_name, _resolve_dataset_name

    example = Path("examples/ticket_triage")
    assert _resolve_dataset_name(example, "triage-v2") == "triage-v2"
    assert _resolve_dataset_name(example, None) == _default_dataset_name(example)


def test_dataset_upload_command_registered() -> None:
    """Dataset upload is available as a nested CLI command."""
    from typer.main import get_command

    from harnesslab.cli.main import app

    command = get_command(app)
    subcommands = command.commands["dataset"].commands
    assert "upload" in subcommands
