"""Bridge legacy scorers to Langfuse experiment evaluators."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langfuse.experiment import Evaluation

from harnesslab.eval.types import EvalExample, EvalRun

LegacyEvaluator = Callable[[EvalRun, EvalExample], dict[str, Any]]


def adapt_evaluator(scorer: LegacyEvaluator):
    """Wrap a legacy (run, example) scorer for Langfuse run_experiment."""

    def evaluator(
        *,
        input: Any,
        output: Any,
        expected_output: Any,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Evaluation:
        _ = metadata, kwargs
        result = scorer(
            EvalRun.from_output(output if isinstance(output, dict) else {"result": output}),
            EvalExample.from_item(input=input, expected_output=expected_output),
        )
        return Evaluation(
            name=str(result["key"]),
            value=result["score"],
            comment=str(result.get("comment") or ""),
        )

    return evaluator
