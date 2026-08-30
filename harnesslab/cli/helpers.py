"""Shared CLI helpers for path resolution, env bootstrap, and run metadata."""

import os
from pathlib import Path

import typer

from harnesslab.config.env import disable_langsmith_tracing, load_local_env
from harnesslab.config.model_catalog import DEFAULT_MODEL

DEFAULT_COMPARE_HARNESSES = "minimal,retry"
DEFAULT_TASK_LIMIT = 1


def bootstrap_env(*, local: bool, example: Path | None = None) -> None:
    """Load .env and disable LangSmith uploads for local-only commands."""
    load_local_env(example=example)
    if local:
        disable_langsmith_tracing()


def default_dataset_name(example: Path) -> str:
    """Derive a stable LangSmith dataset name from an example directory."""
    return f"{example.name.replace('_', '-')}-stress"


def example_paths(example: Path) -> tuple[Path, Path]:
    """Resolve harness and task directories for an example project."""
    harness_dir = example / "harnesses"
    tasks_dir = example / "tasks"
    if not harness_dir.exists() or not tasks_dir.exists():
        raise typer.BadParameter(f"Invalid example path: {example}")
    return harness_dir, tasks_dir


def resolve_task_limit(tasks: int | None, task: str | None) -> int | None:
    """Return task cap; single-ticket runs ignore the default limit."""
    if task is not None:
        return tasks
    return DEFAULT_TASK_LIMIT if tasks is None else tasks


def resolve_dataset_name(example: Path, dataset: str | None) -> str:
    """Return explicit dataset name or the example-derived default."""
    if dataset and dataset.strip():
        return dataset.strip()
    return default_dataset_name(example)


def compare_metadata(
    *,
    example: Path,
    local: bool,
    compare_by: str,
    arms: list[str],
    harness: str | None,
    models: list[str] | None,
    task_count: int,
    tasks: int | None,
    ticket_id: str | None,
    model: str | None = None,
    dataset: str | None = None,
) -> dict:
    """Build metadata persisted alongside local experiment results."""
    return {
        "example": str(example.resolve()),
        "compare_by": compare_by,
        "arms": arms,
        "harness": harness,
        "models": models,
        "langsmith_mode": not local,
        "task_count": task_count,
        "tasks_limit": tasks,
        "ticket_id": ticket_id,
        "model": model or os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL),
        "dataset": dataset,
    }
