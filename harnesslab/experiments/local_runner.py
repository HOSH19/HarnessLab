"""In-process experiment runner for local benchmark and gate commands."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from langsmith.evaluation.evaluator import EvaluationResult, EvaluationResults
from langsmith.schemas import Example, Run

logger = logging.getLogger(__name__)


class LocalExperimentResults(list):
    """List-like experiment results compatible with compare and gate consumers."""

    def __init__(self, rows: list[dict[str, Any]], *, experiment_name: str):
        super().__init__(rows)
        self._experiment_name = experiment_name

    def experiment_name(self) -> str:
        return self._experiment_name


def run_local_experiment(
    target: Callable[[dict], dict],
    data: list[Example],
    evaluators: list[Callable],
    *,
    experiment_prefix: str,
    metadata: dict[str, Any] | None = None,
) -> LocalExperimentResults:
    """Execute target and evaluators without LangSmith evaluate upload_results."""
    rows: list[dict[str, Any]] = []
    meta = metadata or {}

    for example in data:
        inputs = example.inputs or {}
        try:
            outputs = target(inputs)
        except Exception as exc:  # noqa: BLE001 — keep row for downstream evaluators
            logger.error("Local target failed: %s", exc, exc_info=True)
            outputs = {"error": str(exc), "error_count": 1}

        run = Run(
            id=uuid4(),
            name=experiment_prefix,
            run_type="chain",
            start_time=datetime.now(timezone.utc),
            outputs=outputs,
            extra={"metadata": meta},
        )

        eval_results: list[EvaluationResult] = []
        for evaluator in evaluators:
            try:
                result = evaluator(run, example)
            except Exception as exc:  # noqa: BLE001
                key = getattr(evaluator, "__name__", "evaluator")
                result = {
                    "key": key,
                    "score": 0.0,
                    "comment": f"evaluator_error: {exc}",
                }
            if isinstance(result, dict):
                eval_results.append(EvaluationResult(**result))
            else:
                eval_results.append(result)

        rows.append(
            {
                "run": run,
                "example": example,
                "evaluation_results": EvaluationResults(results=eval_results),
            }
        )

    return LocalExperimentResults(rows, experiment_name=experiment_prefix)
