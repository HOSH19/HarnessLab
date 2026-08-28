"""Convert Langfuse experiment results into HarnessLab row dicts."""

from __future__ import annotations

from typing import Any

from langfuse.experiment import ExperimentResult


def _item_fields(item: Any) -> tuple[dict[str, Any], str | None]:
    """Return (inputs, item_id) from a local or hosted dataset item."""
    if isinstance(item, dict):
        return dict(item.get("input") or {}), item.get("id")
    return dict(getattr(item, "input", None) or {}), getattr(item, "id", None)


def experiment_result_to_rows(result: ExperimentResult) -> list[dict[str, Any]]:
    """Convert an ExperimentResult into report/store-compatible rows."""
    rows: list[dict[str, Any]] = []
    for item_result in result.item_results:
        inputs, item_id = _item_fields(item_result.item)
        evaluations = {
            evaluation.name: {
                "score": evaluation.value,
                "comment": str(evaluation.comment or ""),
            }
            for evaluation in item_result.evaluations
        }
        rows.append(
            {
                "example": {"inputs": inputs, "id": item_id},
                "outputs": item_result.output if isinstance(item_result.output, dict) else {},
                "run_id": item_result.trace_id,
                "evaluation_results": evaluations,
            }
        )
    return rows
