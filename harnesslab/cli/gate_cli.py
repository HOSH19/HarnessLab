"""Regression gate and benchmark export commands."""

from pathlib import Path

import typer
from rich.console import Console

from harnesslab.cli.compare_runner import run_harness_compare
from harnesslab.cli.helpers import DEFAULT_COMPARE_HARNESSES
from harnesslab.config.env import LangSmithConfigError
from harnesslab.gate.baseline import build_baseline, load_baseline, write_baseline
from harnesslab.gate.check import check_regression
from harnesslab.report.results import SUMMARY_KEYS

console = Console()


def register_gate_commands(app: typer.Typer) -> None:
    """Register gate and benchmark commands on the root CLI app."""

    @app.command("gate")
    def gate_command(
        example: Path = typer.Argument(..., help="Path to example project"),
        baseline: Path = typer.Option(..., "--baseline", help="Benchmark baseline JSON path"),
        harness: str = typer.Option(DEFAULT_COMPARE_HARNESSES, "--harness"),
        local: bool = typer.Option(True, "--local/--no-local", help="Skip LangSmith upload (default: local)"),
        tasks: int | None = typer.Option(None, "--tasks"),
        task: str | None = typer.Option(None, "--task"),
        max_regression: float = typer.Option(0.05, "--max-regression"),
    ) -> None:
        """Fail when harness scores regress vs a committed baseline."""
        try:
            comparisons = run_harness_compare(
                example,
                harness=harness,
                local=local,
                tasks=tasks,
                task=task,
                dataset=None,
                model=None,
            )
        except LangSmithConfigError as exc:
            raise typer.BadParameter(str(exc)) from exc

        result = check_regression(
            baseline=load_baseline(baseline),
            comparisons=comparisons,
            summary_keys=SUMMARY_KEYS,
            max_regression=max_regression,
        )
        _print_gate_details(result.details)

        if result.passed:
            console.print("[green]Gate passed[/green]")
            return

        for failure in result.failures:
            console.print(f"[red]REGRESSION: {failure}[/red]")
        raise typer.Exit(1)

    @app.command("benchmark")
    def benchmark_command(
        example: Path = typer.Argument(..., help="Path to example project"),
        output: Path = typer.Option(..., "--output", "-o"),
        harness: str = typer.Option(DEFAULT_COMPARE_HARNESSES, "--harness"),
        local: bool = typer.Option(True, "--local/--no-local"),
        tasks: int | None = typer.Option(None, "--tasks"),
        task: str | None = typer.Option(None, "--task"),
    ) -> None:
        """Export compare results as a regression-gate baseline JSON file."""
        comparisons = run_harness_compare(
            example,
            harness=harness,
            local=local,
            tasks=tasks,
            task=task,
            dataset=None,
            model=None,
        )
        payload = build_baseline(
            example=str(example.resolve()),
            comparisons=comparisons,
            summary_keys=SUMMARY_KEYS,
        )
        path = write_baseline(output, payload)
        console.print(f"[green]Baseline written to {path}[/green]")


def _print_gate_details(details: list[dict]) -> None:
    """Print bootstrap delta details for each arm and evaluator."""
    for detail in details:
        console.print(
            f"[dim]{detail['arm']}/{detail['evaluator']}: "
            f"delta={detail['mean_delta']}, "
            f"ci=[{detail['ci_lower']}, {detail['ci_upper']}][/dim]"
        )
