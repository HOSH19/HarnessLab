"""LangSmith experiment orchestration for harness A/B runs.

Runs compiled graphs against task datasets and registers evaluators.
Does not implement scorer logic; delegates to eval package.
"""

import os
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Literal

from langsmith.schemas import Example, Run

from agentevals.graph_trajectory.utils import extract_langgraph_trajectory_from_thread
from langchain_core.messages import AIMessage, HumanMessage
from langsmith import evaluate

from harnesslab.config.env import disable_langsmith_tracing
from harnesslab.config.model_catalog import DEFAULT_MODEL, model_short_name

from harnesslab.flaky import init_flaky_tools

from harnesslab.config.models import HarnessConfig
from harnesslab.middleware.limits import recursion_limit as graph_recursion_limit
from harnesslab.eval.efficiency import efficiency
from harnesslab.eval.error_recovery import error_recovery
from harnesslab.eval.fingerprint import failure_fingerprint
from harnesslab.eval.outcome import task_pass
from harnesslab.eval.trajectory import graph_trajectory
from harnesslab.experiments.dataset import ensure_dataset
from harnesslab.experiments.examples import tasks_to_examples
from harnesslab.experiments.tasks import load_tasks
from harnesslab.graph.extract import extract_fields_from_messages

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

    def wrapped(run: Run, example: Example) -> dict:
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


def _build_initial_messages(prompt: str, conversation_history: list[dict] | None) -> list:
    """Build message list from optional prior turns plus the task prompt."""
    messages: list = []
    for turn in conversation_history or []:
        role = turn.get("role", "human")
        content = turn.get("content", "")
        if role in {"human", "user"}:
            messages.append(HumanMessage(content=content))
        elif role in {"ai", "assistant"}:
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=prompt))
    return messages


def _invoke_config(harness: HarnessConfig, *, model: str | None = None) -> dict:
    """Build LangGraph invoke config with recursion limit and trace tags.

    Trace tags are minimized to harness_name (+ optional user trace_metadata).
    thread_id is required for trajectory extraction but is not a filter tag.
    Model and flaky_tools live on experiment metadata / dataset inputs instead.
    """
    del model
    project = harness.observability.langsmith_project or "harnesslab"
    os.environ["LANGSMITH_PROJECT"] = project

    configurable: dict[str, Any] = {
        "thread_id": str(uuid.uuid4()),
        "harness_name": harness.name,
        **harness.observability.trace_metadata,
    }

    return {
        "configurable": configurable,
        "recursion_limit": graph_recursion_limit(harness.execution),
    }


def _extract_outputs(state: dict, graph: Any, config: dict) -> dict:
    """Pull the minimal evaluation fields from graph state and trajectory."""
    messages = state.get("messages", [])
    parsed = extract_fields_from_messages(messages)
    trajectory = extract_langgraph_trajectory_from_thread(graph, config)
    classification = parsed["classification"] or state.get("classification", "")
    final_reply = parsed["final_reply"] or state.get("final_reply", "")

    return {
        "output": classification or "",
        "classification": classification or "",
        "final_reply": final_reply,
        "graph_trajectory": trajectory["outputs"],
        "error_count": state.get("error_count", 0),
    }


def _empty_outputs(*, error: str | None = None) -> dict:
    """Return a minimal outputs dict when graph invocation fails."""
    payload = {
        "output": "",
        "classification": "",
        "final_reply": "",
        "graph_trajectory": {"steps": [], "results": [], "inputs": []},
        "error_count": 1 if error else 0,
    }
    if error:
        payload["error"] = error
    return payload


def make_target(graph_factory: Callable[[HarnessConfig], Any], harness: HarnessConfig):
    """Create a LangSmith-compatible target function for a harness variant."""
    graph = graph_factory(harness)

    def target(inputs: dict) -> dict:
        """Run the agent on a single task input."""
        prompt = inputs.get("prompt", "")
        ticket_id = inputs.get("ticket_id", "")
        flaky_tools = inputs.get("flaky_tools")
        conversation_history = inputs.get("conversation_history")
        model = os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)
        config = _invoke_config(harness, model=model)
        if flaky_tools:
            config["configurable"]["flaky_tools"] = flaky_tools
        init_flaky_tools(flaky_tools)
        try:
            state = graph.invoke(
                {
                    "messages": _build_initial_messages(prompt, conversation_history),
                    "ticket_id": ticket_id,
                    "classification": "",
                    "final_reply": "",
                    "error_count": 0,
                },
                config=config,
            )
            return _extract_outputs(state, graph, config)
        except Exception as exc:  # noqa: BLE001 — always return outputs for evaluators
            return _empty_outputs(error=str(exc))

    return target


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
