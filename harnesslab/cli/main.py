"""HarnessLab CLI entrypoint.

Registers run, compare, and dataset commands. Delegates logic to
experiments and report modules without embedding business rules.
"""

from pathlib import Path

import typer
from rich.console import Console

from examples.ticket_triage.graph import build_ticket_triage_graph
from harnesslab.config.loader import load_harness_config, load_harness_dir
from harnesslab.experiments.dataset import upload_dataset
from harnesslab.experiments.runner import run_experiment
from harnesslab.report.html import write_report

console = Console()
app = typer.Typer(
    name="harnesslab",
    help="Harness A/B experimentation for LangGraph agents.",
    no_args_is_help=True,
)


def _example_paths(example: Path) -> tuple[Path, Path]:
    """Resolve harness and task directories for an example project."""
    harness_dir = example / "harnesses"
    tasks_dir = example / "tasks"
    if not harness_dir.exists() or not tasks_dir.exists():
        raise typer.BadParameter(f"Invalid example path: {example}")
    return harness_dir, tasks_dir


@app.command("run")
def run_command(
    example: Path = typer.Argument(..., help="Path to example project"),
    harness: str = typer.Option(..., "--harness", "-h", help="Harness config name"),
    local: bool = typer.Option(False, "--local", help="Skip LangSmith upload"),
    tasks: int | None = typer.Option(None, "--tasks", help="Limit number of tasks"),
) -> None:
    """Run one harness variant against all tasks in an example."""
    harness_dir, tasks_dir = _example_paths(example)
    config = load_harness_config(harness_dir / f"{harness}.yaml")

    console.print(f"[bold]Running harness:[/bold] {config.name}")
    results = run_experiment(
        build_ticket_triage_graph,
        config,
        tasks_dir,
        upload_results=not local,
        task_limit=tasks,
    )
    rows = list(results)
    console.print(f"[green]Completed {len(rows)} task(s)[/green]")


@app.command("compare")
def compare_command(
    example: Path = typer.Argument(..., help="Path to example project"),
    harnesses: str = typer.Option(
        "minimal,with_retry,with_context_trim",
        "--harness",
        help="Comma-separated harness names",
    ),
    output: Path = typer.Option(Path("report.html"), "--output", "-o"),
    local: bool = typer.Option(False, "--local", help="Skip LangSmith upload"),
    tasks: int | None = typer.Option(None, "--tasks", help="Limit number of tasks"),
) -> None:
    """Compare multiple harness variants and write an HTML report."""
    harness_dir, tasks_dir = _example_paths(example)
    all_configs = load_harness_dir(harness_dir)
    names = [name.strip() for name in harnesses.split(",") if name.strip()]

    comparisons: dict[str, list] = {}
    for name in names:
        if name not in all_configs:
            raise typer.BadParameter(f"Unknown harness: {name}")
        console.print(f"[bold]Evaluating harness:[/bold] {name}")
        results = run_experiment(
            build_ticket_triage_graph,
            all_configs[name],
            tasks_dir,
            upload_results=not local,
            task_limit=tasks,
        )
        comparisons[name] = list(results)

    report_path = write_report(comparisons, output)
    console.print(f"[green]Report written to {report_path}[/green]")


@app.command("dataset")
def dataset_command(
    example: Path = typer.Argument(..., help="Path to example project"),
    name: str = typer.Option("harnesslab-ticket-triage", "--name", help="Dataset name"),
) -> None:
    """Upload task fixtures to a LangSmith dataset."""
    _, tasks_dir = _example_paths(example)
    dataset_name = upload_dataset(tasks_dir, name)
    console.print(f"[green]Uploaded dataset: {dataset_name}[/green]")


def main() -> None:
    """Run the HarnessLab CLI."""
    app()


if __name__ == "__main__":
    main()
