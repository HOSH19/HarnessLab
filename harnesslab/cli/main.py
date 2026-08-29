"""HarnessLab CLI entrypoint.

Registers run, compare, and dataset commands. Delegates logic to
experiments and report modules without embedding business rules.
"""

import os
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console

from harnesslab.config.env import (
    LangSmithConfigError,
    disable_langsmith_tracing,
    load_local_env,
    validate_langsmith_upload_config,
)
from harnesslab.config.model_catalog import DEFAULT_CHEAP_MODELS, DEFAULT_MODEL, parse_model_list

from harnesslab.config.loader import load_harness_config, load_harness_dir
from harnesslab.examples.loader import load_graph_factory
from harnesslab.experiments.dataset import upload_dataset
from harnesslab.experiments.runner import run_comparison, run_experiment
from harnesslab.experiments.store import save_compare_run, save_experiment_run
from harnesslab.report.html import write_report

console = Console()
app = typer.Typer(
    name="harnesslab",
    help="Harness and model experimentation for LangGraph agents.",
    no_args_is_help=True,
)

CompareBy = Literal["harness", "models"]

DEFAULT_COMPARE_HARNESSES = "minimal,retry"
DEFAULT_TASK_LIMIT = 1


def _bootstrap_env(*, local: bool, example: Path | None = None) -> None:
    """Load .env and disable LangSmith uploads for local-only commands."""
    if local:
        disable_langsmith_tracing()
    load_local_env(example=example)
    if local:
        disable_langsmith_tracing()


def _default_dataset_name(example: Path) -> str:
    """Derive a stable LangSmith dataset name from an example directory."""
    return f"{example.name.replace('_', '-')}-stress"


def _example_paths(example: Path) -> tuple[Path, Path]:
    """Resolve harness and task directories for an example project."""
    harness_dir = example / "harnesses"
    tasks_dir = example / "tasks"
    if not harness_dir.exists() or not tasks_dir.exists():
        raise typer.BadParameter(f"Invalid example path: {example}")
    return harness_dir, tasks_dir


def _resolve_task_limit(tasks: int | None, task: str | None) -> int | None:
    """Return task cap; single-ticket runs ignore the default limit."""
    if task is not None:
        return tasks
    return DEFAULT_TASK_LIMIT if tasks is None else tasks


def _resolve_dataset_name(example: Path, dataset: str | None) -> str:
    """Return explicit dataset name or the example-derived default."""
    if dataset and dataset.strip():
        return dataset.strip()
    return _default_dataset_name(example)


def _compare_metadata(
    *,
    example: Path,
    local: bool,
    compare_by: CompareBy,
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


@app.command("run")
def run_command(
    example: Path = typer.Argument(..., help="Path to example project"),
    harness: str = typer.Option(..., "--harness", "-h", help="Harness config name"),
    local: bool = typer.Option(False, "--local", help="Skip LangSmith upload"),
    tasks: int | None = typer.Option(
        None,
        "--tasks",
        help=f"Limit number of tasks (default: {DEFAULT_TASK_LIMIT}; ignored when --task is set)",
    ),
    task: str | None = typer.Option(None, "--task", help="Single task id (e.g. R-001, I-103)"),
    dataset: str | None = typer.Option(
        None,
        "--dataset",
        help="LangSmith dataset name (default: <example>-stress)",
    ),
    model: str | None = typer.Option(None, "--model", help="Model override for this run"),
    runs_dir: Path = typer.Option(Path(".harnesslab/runs"), "--runs-dir", help="Local results directory"),
) -> None:
    """Run one harness variant against stress tasks."""
    _bootstrap_env(local=local, example=example)
    if not local:
        try:
            validate_langsmith_upload_config()
        except LangSmithConfigError as exc:
            raise typer.BadParameter(str(exc)) from exc

    tasks_limit = _resolve_task_limit(tasks, task)
    ticket_id = task

    resolved_dataset = _resolve_dataset_name(example, dataset)

    harness_dir, tasks_dir = _example_paths(example)
    config = load_harness_config(harness_dir / f"{harness}.yaml")
    resolved_model = model or os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)

    graph_factory = load_graph_factory(example)

    console.print(f"[bold]Running harness:[/bold] {config.name}  [dim]model={resolved_model}[/dim]")
    results = run_experiment(
        graph_factory,
        config,
        tasks_dir,
        upload_results=not local,
        task_limit=tasks_limit,
        ticket_id=ticket_id,
        dataset_name=resolved_dataset,
        model=resolved_model,
    )
    rows = list(results)
    run_path = save_experiment_run(
        resolved_model if model else config.name,
        rows,
        out_dir=runs_dir,
        metadata=_compare_metadata(
            example=example,
            local=local,
            compare_by="harness",
            arms=[config.name],
            harness=config.name,
            models=[resolved_model],
            task_count=len(rows),
            tasks=tasks_limit,
            ticket_id=ticket_id,
            dataset=resolved_dataset,
        ),
    )
    console.print(f"[green]Completed {len(rows)} task(s)[/green]")
    console.print(f"[green]Results saved to {run_path}[/green]")


@app.command("compare")
def compare_command(
    example: Path = typer.Argument(..., help="Path to example project"),
    compare_by: CompareBy = typer.Option(
        "harness",
        "--by",
        help="Compare across harnesses (same model) or models (same harness)",
    ),
    harness: str = typer.Option(
        DEFAULT_COMPARE_HARNESSES,
        "--harness",
        help="Harness name(s); comma-separated when --by harness, single value when --by models",
    ),
    models: str | None = typer.Option(
        None,
        "--models",
        help=f"Cheap models to compare (default: {', '.join(DEFAULT_CHEAP_MODELS)})",
    ),
    output: Path = typer.Option(Path("report.html"), "--output", "-o"),
    local: bool = typer.Option(False, "--local", help="Skip LangSmith upload"),
    tasks: int | None = typer.Option(
        None,
        "--tasks",
        help=f"Limit number of stress tasks (default: {DEFAULT_TASK_LIMIT}; ignored when --task is set)",
    ),
    task: str | None = typer.Option(None, "--task", help="Single task id (e.g. R-001, I-103)"),
    model: str | None = typer.Option(
        None,
        "--model",
        help="Model override (default: HARNESSLAB_MODEL from .env)",
    ),
    dataset: str | None = typer.Option(
        None,
        "--dataset",
        help="LangSmith dataset name (default: <example>-stress)",
    ),
    runs_dir: Path = typer.Option(Path(".harnesslab/runs"), "--runs-dir", help="Local results directory"),
) -> None:
    """Compare models or harness variants on stress tasks and write a report."""
    _bootstrap_env(local=local, example=example)
    if not local:
        try:
            validate_langsmith_upload_config()
        except LangSmithConfigError as exc:
            raise typer.BadParameter(str(exc)) from exc

    tasks_limit = _resolve_task_limit(tasks, task)
    ticket_id = task
    resolved_dataset = _resolve_dataset_name(example, dataset)

    harness_dir, tasks_dir = _example_paths(example)
    all_configs = load_harness_dir(harness_dir)

    if compare_by == "models":
        harness_names = [harness.strip()]
        model_names = parse_model_list(models)
        if harness_names[0] not in all_configs:
            raise typer.BadParameter(f"Unknown harness: {harness_names[0]}")
        console.print(
            f"[bold]Comparing models[/bold] on harness [cyan]{harness_names[0]}[/cyan]: "
            + ", ".join(model_names)
        )
    else:
        harness_names = [name.strip() for name in harness.split(",") if name.strip()]
        model_names = [model or os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)]
        for name in harness_names:
            if name not in all_configs:
                raise typer.BadParameter(f"Unknown harness: {name}")
        console.print(
            f"[bold]Comparing harnesses[/bold] on model [cyan]{model_names[0]}[/cyan]: "
            + ", ".join(harness_names)
            + f"  [dim]dataset={resolved_dataset}[/dim]"
        )

    graph_factory = load_graph_factory(example)

    comparisons = run_comparison(
        graph_factory,
        harness_dir,
        tasks_dir,
        all_configs,
        compare_by=compare_by,
        harness_names=harness_names,
        model_names=model_names,
        upload_results=not local,
        task_limit=tasks_limit,
        ticket_id=ticket_id,
        dataset_name=resolved_dataset,
    )

    dimension = "Model" if compare_by == "models" else "Harness"
    report_path = write_report(comparisons, output, dimension=dimension)
    arms = model_names if compare_by == "models" else harness_names
    run_path = save_compare_run(
        comparisons,
        out_dir=runs_dir,
        metadata=_compare_metadata(
            example=example,
            local=local,
            compare_by=compare_by,
            arms=arms,
            harness=harness_names[0] if compare_by == "models" else None,
            models=model_names if compare_by == "models" else None,
            task_count=len(next(iter(comparisons.values()))) if comparisons else 0,
            tasks=tasks_limit,
            ticket_id=ticket_id,
            model=model_names[0] if compare_by == "harness" else None,
            dataset=resolved_dataset,
        ),
    )
    console.print(f"[green]Report written to {report_path}[/green]")
    console.print(f"[green]Results saved to {run_path}[/green]")


dataset_app = typer.Typer(help="LangSmith dataset commands.", no_args_is_help=True)


def _upload_dataset(example: Path, name: str) -> None:
    """Upload local task fixtures to a LangSmith dataset."""
    load_local_env()
    _, tasks_dir = _example_paths(example)
    dataset_name = upload_dataset(tasks_dir, name)
    console.print(f"[green]Uploaded dataset: {dataset_name}[/green]")


@dataset_app.command("upload")
def dataset_upload_command(
    example: Path = typer.Argument(..., help="Path to example project"),
    name: str = typer.Option("research-stress", "--name", help="Dataset name"),
) -> None:
    """Upload stress task fixtures to a LangSmith dataset."""
    _upload_dataset(example, name)


app.add_typer(dataset_app, name="dataset")


def main() -> None:
    """Run the HarnessLab CLI."""
    app()


if __name__ == "__main__":
    main()
