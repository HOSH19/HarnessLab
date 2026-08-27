"""LangSmith experiment orchestration for harness A/B runs.

Runs compiled graphs against task datasets and registers evaluators.
Does not implement scorer logic; delegates to eval package.
"""

import os
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agentevals.graph_trajectory.utils import extract_langgraph_trajectory_from_thread
from langchain_core.messages import HumanMessage
from langsmith import evaluate

from harnesslab.config.models import HarnessConfig
from harnesslab.eval.efficiency import efficiency
from harnesslab.eval.fingerprint import failure_fingerprint
from harnesslab.eval.outcome import task_pass
from harnesslab.eval.trajectory import graph_trajectory
from harnesslab.experiments.tasks import load_tasks
from harnesslab.graph.extract import extract_fields_from_messages

EVALUATORS = [task_pass, graph_trajectory, efficiency, failure_fingerprint]


def _invoke_config(harness: HarnessConfig) -> dict:
    """Build LangGraph invoke config with recursion limit and metadata."""
    project = harness.observability.langsmith_project or f"harnesslab-{harness.name}"
    os.environ["LANGSMITH_PROJECT"] = project

    return {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
            "harness_name": harness.name,
            **harness.observability.trace_metadata,
        },
        "recursion_limit": harness.execution.max_turns,
    }


def _extract_outputs(state: dict, graph: Any, config: dict) -> dict:
    """Pull evaluation fields from graph state and trajectory history."""
    messages = state.get("messages", [])
    parsed = extract_fields_from_messages(messages)
    trajectory = extract_langgraph_trajectory_from_thread(graph, config)

    return {
        "classification": parsed["classification"] or state.get("classification", ""),
        "final_reply": parsed["final_reply"] or state.get("final_reply", ""),
        "error_count": state.get("error_count", 0),
        "graph_trajectory": trajectory["outputs"],
    }


def make_target(graph_factory: Callable[[HarnessConfig], Any], harness: HarnessConfig):
    """Create a LangSmith-compatible target function for a harness variant.

    Args:
        graph_factory: Callable that returns a compiled graph for a harness.
        harness: Harness configuration for this experiment arm.

    Returns:
        Function mapping dataset inputs to agent outputs.
    """
    graph = graph_factory(harness)

    def target(inputs: dict) -> dict:
        """Run the agent on a single task input."""
        prompt = inputs.get("prompt", "")
        ticket_id = inputs.get("ticket_id", "")
        config = _invoke_config(harness)
        state = graph.invoke(
            {
                "messages": [HumanMessage(content=prompt)],
                "ticket_id": ticket_id,
                "classification": "",
                "final_reply": "",
                "error_count": 0,
            },
            config=config,
        )
        return _extract_outputs(state, graph, config)

    return target


def run_experiment(
    graph_factory: Callable[[HarnessConfig], Any],
    harness: HarnessConfig,
    tasks_dir: Path,
    *,
    upload_results: bool = True,
    max_concurrency: int = 1,
    task_limit: int | None = None,
) -> Any:
    """Run a LangSmith evaluation experiment for one harness variant.

    Args:
        graph_factory: Callable that builds a compiled graph.
        harness: Harness configuration for this arm.
        tasks_dir: Directory with task JSON fixtures.
        upload_results: Whether to upload results to LangSmith.
        max_concurrency: Parallel evaluation limit.
        task_limit: Optional cap on number of tasks to run.

    Returns:
        LangSmith experiment results object.
    """
    data = load_tasks(tasks_dir)
    if task_limit is not None:
        data = data[:task_limit]

    target = make_target(graph_factory, harness)

    return evaluate(
        target,
        data=data,
        evaluators=EVALUATORS,
        experiment_prefix=f"harnesslab-{harness.name}",
        metadata={"harness": harness.model_dump()},
        upload_results=upload_results,
        max_concurrency=max_concurrency,
    )
