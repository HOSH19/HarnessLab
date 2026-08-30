"""LangSmith experiment orchestration for harness A/B runs."""

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Literal

from langsmith import evaluate

from harnesslab.config.env import disable_langsmith_tracing
from harnesslab.config.model_catalog import DEFAULT_MODEL, model_short_name
from harnesslab.config.models import HarnessConfig
from harnesslab.eval.efficiency import efficiency
from harnesslab.eval.error_recovery import error_recovery
from harnesslab.eval.fingerprint import failure_fingerprint
from harnesslab.eval.outcome import task_pass
from harnesslab.eval.trajectory import graph_trajectory
from harnesslab.experiments.dataset import ensure_dataset
from harnesslab.experiments.examples import tasks_to_examples
from harnesslab.experiments.target import make_target
from harnesslab.experiments.tasks import load_tasks

CompareDimension = Literal["harness", "models"]

_BASE_EVALUATORS = [
    task_pass,
    graph_trajectory,
    error_recovery,
    efficiency,
    failure_fingerprint,
]


def _safe_evaluator(evaluator: Callable) -> Callable:
    """Wrap an evaluator so failures still produce feedback in LangSmith."""

    def wrapped(run, example) -> dict:
        try:
            return evaluator(run, example)
        except Exception as exc:  # noqa: BLE001 — evaluators must never abort a row
            key = getattr(evaluator, "__name__", "evaluator")
            return {
                "key": key,
                "score": 0.0,
                "comment": f"evaluator_error: {exc}",
            }

    wrapped.__name__ = getattr(evaluator, "__name__", "wrapped_evaluator")
    return wrapped


EVALUATORS = [_safe_evaluator(fn) for fn in _BASE_EVALUATORS]


@contextmanager
def use_model(model: str | None) -> Iterator[None]:
    """Temporarily set HARNESSLAB_MODEL for one experiment arm."""
    if model is None:
        yield
        return

    previous = os.environ.get("HARNESSLAB_MODEL")
    os.environ["HARNESSLAB_MODEL"] = model
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("HARNESSLAB_MODEL", None)
        else:
            os.environ["HARNESSLAB_MODEL"] = previous


def _resolve_data(
    tasks_dir: Path,
    *,
    upload_results: bool,
    dataset_name: str | None,
    task_limit: int | None,
    ticket_id: str | None,
) -> Any:
    """Build LangSmith evaluate data from local tasks or a remote dataset."""
    if upload_results:
        resolved_dataset = dataset_name or f"{tasks_dir.parent.name.replace('_', '-')}-stress"
        ensure_dataset(
            tasks_dir,
            resolved_dataset,
            task_limit=task_limit,
            ticket_id=ticket_id,
        )
        return resolved_dataset

    data = tasks_to_examples(load_tasks(tasks_dir, ticket_id=ticket_id))
    if task_limit is not None:
        data = data[:task_limit]
    return data


def run_experiment(
    graph_factory: Callable[[HarnessConfig], Any],
    harness: HarnessConfig,
    tasks_dir: Path,
    *,
    upload_results: bool = True,
    max_concurrency: int = 1,
    task_limit: int | None = None,
    ticket_id: str | None = None,
    dataset_name: str | None = None,
    model: str | None = None,
    experiment_prefix: str | None = None,
) -> Any:
    """Run a LangSmith evaluation experiment for one harness variant."""
    prefix = experiment_prefix or harness.name
    metadata: dict[str, Any] = {"harness": harness.model_dump()}
    if model:
        metadata["model"] = model

    with use_model(model):
        data = _resolve_data(
            tasks_dir,
            upload_results=upload_results,
            dataset_name=dataset_name,
            task_limit=task_limit,
            ticket_id=ticket_id,
        )
        target = make_target(graph_factory, harness)

        if not upload_results:
            disable_langsmith_tracing()

        return evaluate(
            target,
            data=data,
            evaluators=EVALUATORS,
            experiment_prefix=prefix,
            metadata=metadata,
            upload_results=upload_results,
            max_concurrency=max_concurrency,
        )


def run_comparison(
    graph_factory: Callable[[HarnessConfig], Any],
    harness_dir: Path,
    tasks_dir: Path,
    all_configs: dict[str, HarnessConfig],
    *,
    compare_by: CompareDimension,
    harness_names: list[str],
    model_names: list[str],
    upload_results: bool = True,
    task_limit: int | None = None,
    ticket_id: str | None = None,
    dataset_name: str | None = None,
) -> dict[str, list]:
    """Run a comparison across harnesses or models."""
    comparisons: dict[str, list] = {}

    if compare_by == "models":
        if len(harness_names) != 1:
            raise ValueError("Model comparisons require exactly one --harness value.")
        harness = all_configs[harness_names[0]]
        for model in model_names:
            results = run_experiment(
                graph_factory,
                harness,
                tasks_dir,
                upload_results=upload_results,
                task_limit=task_limit,
                ticket_id=ticket_id,
                dataset_name=dataset_name,
                model=model,
                experiment_prefix=model_short_name(model),
            )
            comparisons[model] = list(results)
        return comparisons

    fixed_model = os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)
    for name in harness_names:
        if name not in all_configs:
            raise ValueError(f"Unknown harness: {name}")
        with use_model(fixed_model):
            results = run_experiment(
                graph_factory,
                all_configs[name],
                tasks_dir,
                upload_results=upload_results,
                task_limit=task_limit,
                ticket_id=ticket_id,
                dataset_name=dataset_name,
                model=fixed_model,
                experiment_prefix=name,
            )
        comparisons[name] = list(results)
    return comparisons
