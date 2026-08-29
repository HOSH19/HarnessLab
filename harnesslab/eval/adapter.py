"""Adapter between Langfuse experiment evaluators and HarnessLab scorers.

Wraps legacy (run, example) evaluator functions so they can be registered
with langfuse.run_experiment() / dataset.run_experiment().
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable

from langfuse import Evaluation

from harnesslab.eval.efficiency import efficiency
from harnesslab.eval.error_recovery import error_recovery
from harnesslab.eval.final_reply import reply_text
from harnesslab.eval.fingerprint import failure_fingerprint
from harnesslab.eval.outcome import task_pass
from harnesslab.eval.step_count import step_count
from harnesslab.eval.tool_sequence import tool_sequence
from harnesslab.eval.trajectory import graph_trajectory

EvaluatorFn = Callable[..., dict[str, Any]]

_BASE_EVALUATORS: list[EvaluatorFn] = [
    task_pass,
    graph_trajectory,
    tool_sequence,
    error_recovery,
    step_count,
    efficiency,
    failure_fingerprint,
    reply_text,
]


def _item_input(item: Any) -> dict[str, Any]:
    if hasattr(item, "input"):
        value = item.input
    elif isinstance(item, dict):
        value = item.get("input", item)
    else:
        value = item
    return value if isinstance(value, dict) else {"prompt": value}


def _item_expected_output(item: Any, expected_output: Any) -> dict[str, Any]:
    if expected_output is not None:
        return expected_output if isinstance(expected_output, dict) else {"value": expected_output}
    if hasattr(item, "expected_output"):
        value = item.expected_output
        if value is not None:
            return value if isinstance(value, dict) else {"value": value}
    if isinstance(item, dict) and item.get("expected_output") is not None:
        value = item["expected_output"]
        return value if isinstance(value, dict) else {"value": value}
    return {}


def _build_run(output: Any) -> Any:
    """Build a Run-like object from a task output dict."""
    if not isinstance(output, dict):
        output = {}
    metrics = output.get("_run_metrics") or {}
    child_count = int(metrics.get("child_count", 0))
    return SimpleNamespace(
        outputs=output,
        error=output.get("error"),
        total_time=metrics.get("latency_seconds"),
        total_tokens=metrics.get("total_tokens"),
        child_runs=[None] * child_count,
        start_time=metrics.get("start_time"),
        end_time=metrics.get("end_time"),
        extra=metrics.get("extra") or {},
    )


def _build_example(inputs: dict[str, Any], reference: dict[str, Any]) -> Any:
    return SimpleNamespace(inputs=inputs, outputs=reference)


def _result_to_evaluation(result: dict[str, Any]) -> Evaluation:
    return Evaluation(
        name=str(result["key"]),
        value=result["score"],
        comment=str(result.get("comment") or ""),
    )


def wrap_evaluator(evaluator: EvaluatorFn) -> Callable[..., Evaluation]:
    """Wrap a (run, example) scorer for Langfuse experiment evaluators."""

    def langfuse_evaluator(
        *,
        input: Any,
        output: Any,
        expected_output: Any = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Evaluation:
        del metadata, kwargs
        run = _build_run(output)
        example = _build_example(
            input if isinstance(input, dict) else {"prompt": input},
            _item_expected_output({"input": input}, expected_output),
        )
        try:
            result = evaluator(run, example)
        except Exception as exc:  # noqa: BLE001 — evaluators must never abort a row
            key = getattr(evaluator, "__name__", "evaluator")
            return Evaluation(
                name=key,
                value=0.0,
                comment=f"evaluator_error: {exc}",
            )
        return _result_to_evaluation(result)

    langfuse_evaluator.__name__ = getattr(evaluator, "__name__", "langfuse_evaluator")
    return langfuse_evaluator


LANGFUSE_EVALUATORS = [wrap_evaluator(fn) for fn in _BASE_EVALUATORS]
