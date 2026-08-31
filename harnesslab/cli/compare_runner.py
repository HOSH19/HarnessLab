"""Run harness-dimension comparisons for gate and benchmark commands."""

from __future__ import annotations

import os
from pathlib import Path

import typer

from harnesslab.cli.helpers import bootstrap_env, example_paths, resolve_dataset_name, resolve_task_limit
from harnesslab.config.env import validate_langsmith_upload_config
from harnesslab.config.loader import load_harness_dir
from harnesslab.config.model_catalog import DEFAULT_MODEL
from harnesslab.examples.loader import load_graph_factory
from harnesslab.experiments.runner import run_comparison


def parse_harness_names(harness: str) -> list[str]:
    """Split a comma-separated harness list into trimmed names."""
    return [name.strip() for name in harness.split(",") if name.strip()]


def validate_harness_names(names: list[str], all_configs: dict) -> None:
    """Raise when any harness name is missing from the example config set."""
    for name in names:
        if name not in all_configs:
            raise typer.BadParameter(f"Unknown harness: {name}")


def run_harness_compare(
    example: Path,
    *,
    harness: str,
    local: bool,
    tasks: int | None,
    task: str | None,
    dataset: str | None,
    model: str | None,
) -> dict[str, list]:
    """Run a harness-only compare and return per-arm experiment rows."""
    bootstrap_env(local=local, example=example)
    if not local:
        validate_langsmith_upload_config()

    harness_dir, tasks_dir = example_paths(example)
    all_configs = load_harness_dir(harness_dir)
    harness_names = parse_harness_names(harness)
    validate_harness_names(harness_names, all_configs)

    return run_comparison(
        load_graph_factory(example),
        harness_dir,
        tasks_dir,
        all_configs,
        compare_by="harness",
        harness_names=harness_names,
        model_names=[model or os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)],
        upload_results=not local,
        task_limit=resolve_task_limit(tasks, task),
        ticket_id=task,
        dataset_name=resolve_dataset_name(example, dataset),
    )
