"""HarnessLab CLI entrypoint."""

import os
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console

from harnesslab.cli.helpers import (
    DEFAULT_COMPARE_HARNESSES,
    DEFAULT_TASK_LIMIT,
    bootstrap_env,
    compare_metadata,
    example_paths,
    resolve_dataset_name,
    resolve_task_limit,
)
from harnesslab.config.env import LangSmithConfigError, load_local_env, validate_langsmith_upload_config
from harnesslab.config.loader import load_harness_config, load_harness_dir
from harnesslab.config.model_catalog import DEFAULT_CHEAP_MODELS, DEFAULT_MODEL, parse_model_list
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
    bootstrap_env(local=local, example=example)
    if not local:
        try:
            validate_langsmith_upload_config()
        except LangSmithConfigError as exc:
            raise typer.BadParameter(str(exc)) from exc

    tasks_limit = resolve_task_limit(tasks, task)
    resolved_dataset = resolve_dataset_name(example, dataset)
    harness_dir, tasks_dir = example_paths(example)
    config = load_harness_config(harness_dir / f"{harness}.yaml")
    resolved_model = model or os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)

    console.print(f"[bold]Running harness:[/bold] {config.name}  [dim]model={resolved_model}[/dim]")
    results = run_experiment(
        load_graph_factory(example),
        config,
        tasks_dir,
        upload_results=not local,
        task_limit=tasks_limit,
        ticket_id=task,
        dataset_name=resolved_dataset,
        model=resolved_model,
    )
    rows = list(results)
    run_path = save_experiment_run(
        resolved_model if model else config.name,
        rows,
        out_dir=runs_dir,
        metadata=compare_metadata(
            example=example,
            local=local,
            compare_by="harness",
            arms=[config.name],
            harness=config.name,
            models=[resolved_model],
            task_count=len(rows),
            tasks=tasks_limit,
            ticket_id=task,
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
    bootstrap_env(local=local, example=example)
    if not local:
        try:
            validate_langsmith_upload_config()
        except LangSmithConfigError as exc:
            raise typer.BadParameter(str(exc)) from exc

    tasks_limit = resolve_task_limit(tasks, task)
    resolved_dataset = resolve_dataset_name(example, dataset)
    harness_dir, tasks_dir = example_paths(example)
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

    comparisons = run_comparison(
        load_graph_factory(example),
        harness_dir,
        tasks_dir,
        all_configs,
        compare_by=compare_by,
        harness_names=harness_names,
        model_names=model_names,
        upload_results=not local,
        task_limit=tasks_limit,
        ticket_id=task,
        dataset_name=resolved_dataset,
    )

    dimension = "Model" if compare_by == "models" else "Harness"
    report_path = write_report(comparisons, output, dimension=dimension)
    arms = model_names if compare_by == "models" else harness_names
    run_path = save_compare_run(
        comparisons,
        out_dir=runs_dir,
        metadata=compare_metadata(
            example=example,
            local=local,
            compare_by=compare_by,
            arms=arms,
            harness=harness_names[0] if compare_by == "models" else None,
            models=model_names if compare_by == "models" else None,
            task_count=len(next(iter(comparisons.values()))) if comparisons else 0,
            tasks=tasks_limit,
            ticket_id=task,
            model=model_names[0] if compare_by == "harness" else None,
            dataset=resolved_dataset,
        ),
    )
    console.print(f"[green]Report written to {report_path}[/green]")
    console.print(f"[green]Results saved to {run_path}[/green]")


dataset_app = typer.Typer(help="LangSmith dataset commands.", no_args_is_help=True)


@dataset_app.command("upload")
def dataset_upload_command(
    example: Path = typer.Argument(..., help="Path to example project"),
    name: str | None = typer.Option(None, "--name", help="Dataset name (default: <example>-stress)"),
) -> None:
    """Upload stress task fixtures to a LangSmith dataset."""
    load_local_env()
    _, tasks_dir = example_paths(example)
    dataset_name = resolve_dataset_name(example, name)
    console.print(f"[green]Uploaded dataset: {upload_dataset(tasks_dir, dataset_name)}[/green]")


app.add_typer(dataset_app, name="dataset")


def main() -> None:
    """Run the HarnessLab CLI."""
    app()


if __name__ == "__main__":
    main()
