"""Langfuse experiment orchestration for harness A/B runs.

Runs compiled graphs against task datasets and registers evaluators.
Does not implement scorer logic; delegates to eval package.
"""

from __future__ import annotations

import os
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal

from agentevals.graph_trajectory.utils import extract_langgraph_trajectory_from_thread
from langchain_core.messages import AIMessage, HumanMessage
from langfuse import get_client

from harnesslab.config.env import disable_langfuse_tracing
from harnesslab.config.model_catalog import DEFAULT_MODEL, model_short_name
from harnesslab.config.models import HarnessConfig
from harnesslab.eval.adapter import LANGFUSE_EVALUATORS, _item_input
from harnesslab.eval.run_metrics import trajectory_agent_tool_steps
from harnesslab.experiments.dataset import ensure_dataset
from harnesslab.experiments.examples import tasks_to_examples
from harnesslab.experiments.tasks import load_tasks
from harnesslab.graph.extract import extract_fields_from_messages
from harnesslab.middleware.limits import recursion_limit as graph_recursion_limit

from examples.ticket_triage.flaky import init_flaky_tools

CompareDimension = Literal["harness", "models"]


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


def _invoke_config(
    harness: HarnessConfig,
    *,
    model: str | None = None,
    trace_enabled: bool,
) -> dict:
    """Build LangGraph invoke config with recursion limit and trace tags.

    Trace tags are minimized to harness_name (+ optional user trace_metadata).
    thread_id is required for trajectory extraction but is not a filter tag.
    Model and flaky_tools live on experiment metadata / dataset inputs instead.
    """
    del model
    project = harness.observability.langfuse_project or "triage"
    configurable: dict[str, Any] = {
        "thread_id": str(uuid.uuid4()),
        "harness_name": harness.name,
        **harness.observability.trace_metadata,
    }

    config: dict[str, Any] = {
        "configurable": configurable,
        "recursion_limit": graph_recursion_limit(harness.execution),
    }

    if trace_enabled:
        from langfuse.langchain import CallbackHandler

        tags = [project, harness.name]
        config["callbacks"] = [CallbackHandler()]
        config["metadata"] = {
            **harness.observability.trace_metadata,
            "langfuse_tags": tags,
        }

    return config


def _extract_outputs(state: dict, graph: Any, config: dict) -> dict:
    """Pull the minimal evaluation fields from graph state and trajectory."""
    messages = state.get("messages", [])
    parsed = extract_fields_from_messages(messages)
    trajectory = extract_langgraph_trajectory_from_thread(graph, config)
    classification = parsed["classification"] or state.get("classification", "")
    final_reply = parsed["final_reply"] or state.get("final_reply", "")

    return {
        "classification": classification or "",
        "final_reply": final_reply,
        "graph_trajectory": trajectory["outputs"],
        "error_count": state.get("error_count", 0),
    }


def _empty_outputs(*, error: str | None = None) -> dict:
    """Return a minimal outputs dict when graph invocation fails."""
    payload = {
        "classification": "",
        "final_reply": "",
        "graph_trajectory": {"steps": [], "results": [], "inputs": []},
        "error_count": 1 if error else 0,
    }
    if error:
        payload["error"] = error
    return payload


def _attach_run_metrics(outputs: dict, *, elapsed_seconds: float) -> dict:
    """Attach timing and step metadata for efficiency evaluators."""
    graph_steps = trajectory_agent_tool_steps(outputs)
    outputs["_run_metrics"] = {
        "latency_seconds": elapsed_seconds,
        "total_tokens": 0,
        "child_count": graph_steps,
    }
    return outputs


def make_target(
    graph_factory: Callable[[HarnessConfig], Any],
    harness: HarnessConfig,
    *,
    trace_enabled: bool,
):
    """Create a Langfuse-compatible task function for a harness variant."""
    graph = graph_factory(harness)

    def target(*, item, **kwargs) -> dict:
        """Run the agent on a single task input."""
        del kwargs
        inputs = _item_input(item)
        prompt = inputs.get("prompt", "")
        ticket_id = inputs.get("ticket_id", "")
        flaky_tools = inputs.get("flaky_tools")
        conversation_history = inputs.get("conversation_history")
        model = os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)
        config = _invoke_config(harness, model=model, trace_enabled=trace_enabled)
        if flaky_tools:
            config["configurable"]["flaky_tools"] = flaky_tools
        init_flaky_tools(flaky_tools)
        started = time.perf_counter()
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
            outputs = _extract_outputs(state, graph, config)
        except Exception as exc:  # noqa: BLE001 — always return outputs for evaluators
            outputs = _empty_outputs(error=str(exc))
        return _attach_run_metrics(outputs, elapsed_seconds=time.perf_counter() - started)

    return target


def _resolve_data(
    tasks_dir: Path,
    *,
    upload_results: bool,
    dataset_name: str | None,
    task_limit: int | None,
    ticket_id: str | None,
) -> Any:
    """Build Langfuse experiment data from local tasks or a remote dataset."""
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


def _experiment_metadata(harness: HarnessConfig, model: str | None) -> dict[str, str]:
    """Build Langfuse experiment metadata.

    Langfuse propagates metadata as per-key attributes with a 200-character
    limit on each value. Keep entries short scalars, not serialized configs.
    """
    metadata: dict[str, str] = {
        "harness_name": harness.name,
        "langfuse_project": harness.observability.langfuse_project or "triage",
        "max_turns": str(harness.execution.max_turns),
        "retry_count": str(harness.tooling.retry_count),
        "history_limit": (
            str(harness.context.history_limit)
            if harness.context.history_limit is not None
            else ""
        ),
    }
    if model:
        metadata["model"] = model
    return metadata


def _item_id(item: Any) -> str | None:
    if hasattr(item, "id"):
        return str(item.id)
    if isinstance(item, dict):
        metadata = item.get("metadata") or {}
        if isinstance(metadata, dict) and metadata.get("id"):
            return str(metadata["id"])
    return None


def _result_rows(experiment_result: Any) -> list[Any]:
    """Convert Langfuse ExperimentResult rows into store-compatible objects."""
    rows: list[Any] = []
    for item_result in experiment_result.item_results:
        item = item_result.item
        inputs = _item_input(item)
        expected = getattr(item, "expected_output", None)
        if expected is None and isinstance(item, dict):
            expected = item.get("expected_output")

        evaluation_results = {
            "results": [
                {
                    "key": evaluation.name,
                    "score": evaluation.value,
                    "comment": evaluation.comment or "",
                }
                for evaluation in item_result.evaluations
            ]
        }

        rows.append(
            SimpleNamespace(
                example=SimpleNamespace(
                    inputs=inputs,
                    outputs=expected or {},
                    id=_item_id(item),
                ),
                run=SimpleNamespace(
                    id=item_result.trace_id,
                    outputs=item_result.output,
                ),
                outputs=item_result.output,
                run_id=item_result.trace_id,
                evaluation_results=evaluation_results,
            )
        )
    return rows


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
) -> list[Any]:
    """Run a Langfuse evaluation experiment for one harness variant."""
    prefix = experiment_prefix or harness.name
    trace_enabled = upload_results
    if not upload_results:
        disable_langfuse_tracing()

    langfuse = get_client()
    metadata = _experiment_metadata(harness, model)

    with use_model(model):
        data = _resolve_data(
            tasks_dir,
            upload_results=upload_results,
            dataset_name=dataset_name,
            task_limit=task_limit,
            ticket_id=ticket_id,
        )
        task = make_target(graph_factory, harness, trace_enabled=trace_enabled)

        if upload_results and isinstance(data, str):
            dataset = langfuse.get_dataset(data)
            experiment_result = dataset.run_experiment(
                name=prefix,
                task=task,
                evaluators=LANGFUSE_EVALUATORS,
                metadata=metadata,
                max_concurrency=max_concurrency,
            )
        else:
            experiment_result = langfuse.run_experiment(
                name=prefix,
                data=data,
                task=task,
                evaluators=LANGFUSE_EVALUATORS,
                metadata=metadata,
                max_concurrency=max_concurrency,
            )

        return _result_rows(experiment_result)


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
            comparisons[model] = results
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
        comparisons[name] = results
    return comparisons
