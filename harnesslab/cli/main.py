"""HarnessLab CLI entrypoint — registers Typer commands."""

import os
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console

from harnesslab.cli.gate_cli import register_gate_commands
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


def _validate_langsmith_or_raise(local: bool) -> None:
    """Validate LangSmith credentials when uploads are enabled."""
    if local:
        return
    try:
        validate_langsmith_upload_config()
    except LangSmithConfigError as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command("run")
def run_command(
    example: Path = typer.Argument(..., help="Path to example project"),
    harness: str = typer.Option(..., "--harness", "-h"),
    local: bool = typer.Option(False, "--local"),
    tasks: int | None = typer.Option(None, "--tasks"),
    task: str | None = typer.Option(None, "--task"),
    dataset: str | None = typer.Option(None, "--dataset"),
    model: str | None = typer.Option(None, "--model"),
    runs_dir: Path = typer.Option(Path(".harnesslab/runs"), "--runs-dir"),
) -> None:
    """Run one harness variant against stress tasks."""
    bootstrap_env(local=local, example=example)
    _validate_langsmith_or_raise(local)

    harness_dir, tasks_dir = example_paths(example)
    config = load_harness_config(harness_dir / f"{harness}.yaml")
    resolved_model = model or os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)
    resolved_dataset = resolve_dataset_name(example, dataset)
    tasks_limit = resolve_task_limit(tasks, task)

    console.print(f"[bold]Running harness:[/bold] {config.name}  [dim]model={resolved_model}[/dim]")
    rows = list(
        run_experiment(
            load_graph_factory(example),
            config,
            tasks_dir,
            upload_results=not local,
            task_limit=tasks_limit,
            ticket_id=task,
            dataset_name=resolved_dataset,
            model=resolved_model,
        )
    )
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
    compare_by: CompareBy = typer.Option("harness", "--by"),
    harness: str = typer.Option(DEFAULT_COMPARE_HARNESSES, "--harness"),
    models: str | None = typer.Option(None, "--models"),
    output: Path = typer.Option(Path("report.html"), "--output", "-o"),
    local: bool = typer.Option(False, "--local"),
    tasks: int | None = typer.Option(None, "--tasks"),
    task: str | None = typer.Option(None, "--task"),
    model: str | None = typer.Option(None, "--model"),
    dataset: str | None = typer.Option(None, "--dataset"),
    runs_dir: Path = typer.Option(Path(".harnesslab/runs"), "--runs-dir"),
) -> None:
    """Compare harnesses or models and write an HTML report."""
    bootstrap_env(local=local, example=example)
    _validate_langsmith_or_raise(local)

    harness_dir, tasks_dir = example_paths(example)
    all_configs = load_harness_dir(harness_dir)
    harness_names, model_names = _resolve_compare_arms(
        compare_by, harness, models, model, all_configs
    )
    _print_compare_banner(compare_by, harness_names, model_names, resolve_dataset_name(example, dataset))

    comparisons = run_comparison(
        load_graph_factory(example),
        harness_dir,
        tasks_dir,
        all_configs,
        compare_by=compare_by,
        harness_names=harness_names,
        model_names=model_names,
        upload_results=not local,
        task_limit=resolve_task_limit(tasks, task),
        ticket_id=task,
        dataset_name=resolve_dataset_name(example, dataset),
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
            tasks=resolve_task_limit(tasks, task),
            ticket_id=task,
            model=model_names[0] if compare_by == "harness" else None,
            dataset=resolve_dataset_name(example, dataset),
        ),
    )
    console.print(f"[green]Report written to {report_path}[/green]")
    console.print(f"[green]Results saved to {run_path}[/green]")


def _resolve_compare_arms(
    compare_by: CompareBy,
    harness: str,
    models: str | None,
    model: str | None,
    all_configs: dict,
) -> tuple[list[str], list[str]]:
    """Parse and validate harness and model arms for a compare run."""
    if compare_by == "models":
        harness_names = [harness.strip()]
        model_names = parse_model_list(models)
        if harness_names[0] not in all_configs:
            raise typer.BadParameter(f"Unknown harness: {harness_names[0]}")
        return harness_names, model_names

    harness_names = [name.strip() for name in harness.split(",") if name.strip()]
    for name in harness_names:
        if name not in all_configs:
            raise typer.BadParameter(f"Unknown harness: {name}")
    return harness_names, [model or os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)]


def _print_compare_banner(
    compare_by: CompareBy,
    harness_names: list[str],
    model_names: list[str],
    dataset_name: str,
) -> None:
    """Print a short summary of the compare configuration."""
    if compare_by == "models":
        console.print(
            f"[bold]Comparing models[/bold] on harness [cyan]{harness_names[0]}[/cyan]: "
            + ", ".join(model_names)
        )
        return
    console.print(
        f"[bold]Comparing harnesses[/bold] on model [cyan]{model_names[0]}[/cyan]: "
        + ", ".join(harness_names)
        + f"  [dim]dataset={dataset_name}[/dim]"
    )


dataset_app = typer.Typer(help="LangSmith dataset commands.", no_args_is_help=True)


@dataset_app.command("upload")
def dataset_upload_command(
    example: Path = typer.Argument(...),
    name: str | None = typer.Option(None, "--name"),
) -> None:
    """Upload stress task fixtures to a LangSmith dataset."""
    load_local_env()
    _, tasks_dir = example_paths(example)
    dataset_name = resolve_dataset_name(example, name)
    console.print(f"[green]Uploaded dataset: {upload_dataset(tasks_dir, dataset_name)}[/green]")


app.add_typer(dataset_app, name="dataset")
register_gate_commands(app)


def main() -> None:
    """Run the HarnessLab CLI."""
    app()


if __name__ == "__main__":
    main()
