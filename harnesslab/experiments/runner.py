"""Langfuse experiment orchestration for harness A/B runs."""

import os
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Literal

from agentevals.graph_trajectory.utils import extract_langgraph_trajectory_from_thread
from langchain_core.messages import AIMessage, HumanMessage
from langfuse import get_client
from langfuse.langchain import CallbackHandler

from harnesslab.config.env import disable_langfuse_tracing
from harnesslab.config.model_catalog import DEFAULT_MODEL, model_short_name
from examples.ticket_triage.flaky import init_flaky_tools
from harnesslab.config.models import HarnessConfig
from harnesslab.eval.adapter import adapt_evaluator
from harnesslab.eval.efficiency import efficiency
from harnesslab.eval.error_recovery import error_recovery
from harnesslab.eval.fingerprint import failure_fingerprint
from harnesslab.eval.outcome import task_pass
from harnesslab.eval.step_count import step_count
from harnesslab.eval.tool_sequence import tool_sequence
from harnesslab.eval.trajectory import _flatten_steps, graph_trajectory
from harnesslab.experiments.dataset import ensure_dataset
from harnesslab.experiments.examples import tasks_to_local_items
from harnesslab.experiments.results import experiment_result_to_rows
from harnesslab.experiments.tasks import load_tasks
from harnesslab.graph.extract import extract_fields_from_messages
from harnesslab.middleware.limits import recursion_limit as graph_recursion_limit

CompareDimension = Literal["harness", "models"]

LEGACY_EVALUATORS = [
    task_pass,
    graph_trajectory,
    tool_sequence,
    error_recovery,
    step_count,
    efficiency,
    failure_fingerprint,
]

EVALUATORS = [adapt_evaluator(scorer) for scorer in LEGACY_EVALUATORS]


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
    handler: CallbackHandler | None = None,
) -> dict:
    """Build LangGraph invoke config with recursion limit and tracing."""
    session = harness.observability.langfuse_session or "triage"

    configurable: dict[str, Any] = {
        "thread_id": str(uuid.uuid4()),
        "harness_name": harness.name,
        **harness.observability.trace_metadata,
    }
    if model:
        configurable["model"] = model

    config: dict[str, Any] = {
        "configurable": configurable,
        "recursion_limit": graph_recursion_limit(harness.execution),
        "run_name": f"{harness.name}-{session}",
        "metadata": {
            "langfuse_session_id": session,
            "langfuse_tags": [harness.name, model or os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)],
        },
    }
    if handler is not None:
        config["callbacks"] = [handler]
    return config


def _extract_outputs(state: dict, graph: Any, config: dict) -> dict:
    """Pull evaluation fields from graph state and trajectory history."""
    messages = state.get("messages", [])
    parsed = extract_fields_from_messages(messages)
    trajectory = extract_langgraph_trajectory_from_thread(graph, config)
    graph_trajectory_payload = trajectory["outputs"]

    return {
        "classification": parsed["classification"] or state.get("classification", ""),
        "final_reply": parsed["final_reply"] or state.get("final_reply", ""),
        "error_count": state.get("error_count", 0),
        "messages": messages,
        "graph_trajectory": graph_trajectory_payload,
        "_child_count": len(_flatten_steps(graph_trajectory_payload)),
    }


def make_task(graph_factory: Callable[[HarnessConfig], Any], harness: HarnessConfig):
    """Create a Langfuse-compatible task function for a harness variant."""
    graph = graph_factory(harness)

    def task(*, item, **kwargs) -> dict:
        """Run the agent on a single dataset item."""
        _ = kwargs
        inputs = item["input"] if isinstance(item, dict) else item.input
        prompt = inputs.get("prompt", "")
        ticket_id = inputs.get("ticket_id", "")
        flaky_tools = inputs.get("flaky_tools")
        conversation_history = inputs.get("conversation_history")
        model = os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)

        handler = CallbackHandler()
        config = _invoke_config(harness, model=model, handler=handler)
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
        except Exception as exc:
            outputs = {"_error": str(exc), "error_count": 1}
        outputs["_latency_ms"] = (time.perf_counter() - started) * 1000
        return outputs

    return task


def _resolve_local_data(
    tasks_dir: Path,
    *,
    task_limit: int | None,
    ticket_id: str | None,
) -> list[dict[str, Any]]:
    """Build local experiment items from task JSON fixtures."""
    tasks = load_tasks(tasks_dir, ticket_id=ticket_id)
    if task_limit is not None:
        tasks = tasks[:task_limit]
    return tasks_to_local_items(tasks)


def _run_langfuse_experiment(
    *,
    data: Any,
    task,
    experiment_name: str,
    run_name: str,
    metadata: dict[str, Any],
    max_concurrency: int,
    upload_results: bool,
) -> list[dict[str, Any]]:
    """Execute a Langfuse experiment and return normalized result rows."""
    langfuse = get_client()

    if not upload_results:
        disable_langfuse_tracing()

    metadata_str = {str(key): str(value) for key, value in metadata.items()}

    if isinstance(data, str):
        dataset = langfuse.get_dataset(data)
        result = dataset.run_experiment(
            name=experiment_name,
            run_name=run_name,
            task=task,
            evaluators=EVALUATORS,
            max_concurrency=max_concurrency,
            metadata=metadata_str,
        )
    else:
        result = langfuse.run_experiment(
            name=experiment_name,
            run_name=run_name,
            data=data,
            task=task,
            evaluators=EVALUATORS,
            max_concurrency=max_concurrency,
            metadata=metadata_str,
        )

    langfuse.flush()
    return experiment_result_to_rows(result)


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
) -> list[dict[str, Any]]:
    """Run a Langfuse evaluation experiment for one harness variant."""
    prefix = experiment_prefix or harness.name
    metadata: dict[str, Any] = {"harness": harness.name}
    if model:
        metadata["model"] = model

    with use_model(model):
        if upload_results:
            resolved_dataset = dataset_name or f"{tasks_dir.parent.name.replace('_', '-')}-stress"
            ensure_dataset(
                tasks_dir,
                resolved_dataset,
                task_limit=task_limit,
                ticket_id=ticket_id,
            )
            data: Any = resolved_dataset
        else:
            data = _resolve_local_data(tasks_dir, task_limit=task_limit, ticket_id=ticket_id)

        task = make_task(graph_factory, harness)
        return _run_langfuse_experiment(
            data=data,
            task=task,
            experiment_name="harnesslab",
            run_name=prefix,
            metadata=metadata,
            max_concurrency=max_concurrency,
            upload_results=upload_results,
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
            rows = run_experiment(
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
            comparisons[model] = rows
        return comparisons

    fixed_model = os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)
    for name in harness_names:
        if name not in all_configs:
            raise ValueError(f"Unknown harness: {name}")
        with use_model(fixed_model):
            rows = run_experiment(
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
        comparisons[name] = rows
    return comparisons
