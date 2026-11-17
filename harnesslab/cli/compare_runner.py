"""Run harness- or graph-dimension comparisons for gate and benchmark commands."""

from __future__ import annotations

import os
from pathlib import Path

import typer

from harnesslab.cli.helpers import (
    bootstrap_env,
    example_graphs_dir,
    example_paths,
    parse_name_list,
    resolve_dataset_name,
    resolve_task_limit,
)
from harnesslab.config.env import validate_langsmith_upload_config
from harnesslab.config.graph_loader import default_react_graph, load_graph_dir
from harnesslab.config.loader import load_harness_dir
from harnesslab.config.model_catalog import DEFAULT_MODEL
from harnesslab.examples.loader import load_graph_factory
from harnesslab.experiments.runner import CompareDimension, run_comparison


def parse_harness_names(harness: str) -> list[str]:
    """Split a comma-separated harness list into trimmed names."""
    return parse_name_list(harness)


def validate_harness_names(names: list[str], all_configs: dict) -> None:
    """Raise when any harness name is missing from the example config set."""
    for name in names:
        if name not in all_configs:
            raise typer.BadParameter(f"Unknown harness: {name}")


def _load_graphs(example: Path) -> dict:
    """Load graph presets for an example, defaulting to react."""
    graphs_dir = example_graphs_dir(example)
    if graphs_dir.exists():
        configs = load_graph_dir(graphs_dir)
        if configs:
            return configs
    react = default_react_graph()
    return {react.name: react}


def run_harness_compare(
    example: Path,
    *,
    harness: str,
    local: bool,
    tasks: int | None,
    task: str | None,
    dataset: str | None,
    model: str | None,
    compare_by: CompareDimension = "harness",
    graph: str | None = None,
) -> dict[str, list]:
    """Run a harness- or graph-dimension compare and return per-arm rows."""
    bootstrap_env(local=local, example=example)
    if not local:
        validate_langsmith_upload_config()

    harness_dir, tasks_dir = example_paths(example)
    all_configs = load_harness_dir(harness_dir)
    all_graphs = _load_graphs(example)

    if compare_by == "graphs":
        harness_names = [parse_harness_names(harness)[0]]
        validate_harness_names(harness_names, all_configs)
        graph_names = parse_name_list(graph or "react,pipeline")
        for name in graph_names:
            if name not in all_graphs:
                raise typer.BadParameter(f"Unknown graph: {name}")
        return run_comparison(
            load_graph_factory(example),
            harness_dir,
            tasks_dir,
            all_configs,
            compare_by="graphs",
            harness_names=harness_names,
            model_names=[model or os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)],
            upload_results=not local,
            task_limit=resolve_task_limit(tasks, task),
            ticket_id=task,
            dataset_name=resolve_dataset_name(example, dataset),
            graph_configs=all_graphs,
            graph_names=graph_names,
        )

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
