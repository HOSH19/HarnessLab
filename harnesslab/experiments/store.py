"""Local persistence for HarnessLab experiment results."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from harnesslab.config.model_catalog import model_slug
from harnesslab.report.results import SUMMARY_KEYS, evaluation_results, harness_summary, row_value


def _arm_filename(arm: str) -> str:
    """Return a safe filename stem for a comparison arm."""
    return model_slug(arm) if "." in arm else arm


def _to_json_serializable(value: Any) -> Any:
    """Convert nested objects into JSON-safe values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _to_json_serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_serializable(item) for item in value]
    if hasattr(value, "model_dump"):
        return _to_json_serializable(value.model_dump())
    if hasattr(value, "__dict__"):
        return _to_json_serializable(vars(value))
    return str(value)


def serialize_result_row(row: Any) -> dict[str, Any]:
    """Convert a LangSmith experiment result row to a JSON-serializable dict."""
    example = row_value(row, "example", {}) or {}
    example_inputs = getattr(example, "inputs", None) or example.get("inputs", {}) or {}
    example_id = getattr(example, "id", None) or example.get("id")

    outputs = row_value(row, "outputs", {}) or {}
    run = row_value(row, "run", None)
    run_id = row_value(row, "run_id")
    if run is not None:
        run_id = getattr(run, "id", None) or (run.get("id") if isinstance(run, dict) else run_id)

    evaluations: dict[str, dict[str, Any]] = {}
    for result in evaluation_results(row):
        result_key = getattr(result, "key", None) or result.get("key")
        if not result_key:
            continue
        result_score = getattr(result, "score", None)
        if result_score is None and isinstance(result, dict):
            result_score = result.get("score")
        comment = getattr(result, "comment", None)
        if comment is None and isinstance(result, dict):
            comment = result.get("comment")
        evaluations[str(result_key)] = {
            "score": result_score,
            "comment": str(comment or ""),
        }

    return {
        "example_id": str(example_id) if example_id is not None else None,
        "run_id": str(run_id) if run_id is not None else None,
        "inputs": _to_json_serializable(example_inputs),
        "outputs": _to_json_serializable(outputs),
        "evaluation_results": evaluations,
    }


def _timestamp_slug() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _task_count(rows: list) -> int:
    return len(rows)


def _build_manifest(
    *,
    arms: list[str],
    task_count: int,
    metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "arms": arms,
        "task_count": task_count,
    }
    if metadata:
        manifest.update(metadata)
    # Backward-compatible alias for harness-only runs.
    if "harnesses" not in manifest and metadata and metadata.get("compare_by") == "harness":
        manifest["harnesses"] = arms
    return manifest


def save_experiment_run(
    harness_name: str,
    rows: list,
    *,
    out_dir: Path,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Write a single-harness experiment run bundle to disk."""
    run_dir = out_dir / f"{_timestamp_slug()}_{_arm_filename(harness_name)}"
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = _build_manifest(
        arms=[harness_name],
        task_count=_task_count(rows),
        metadata=metadata,
    )
    _write_json(run_dir / "manifest.json", manifest)
    file_stem = _arm_filename(harness_name)
    _write_json(run_dir / f"{file_stem}.json", [serialize_result_row(row) for row in rows])
    _write_json(run_dir / "summary.json", {harness_name: harness_summary(rows)})
    return run_dir.resolve()


def save_compare_run(
    comparisons: dict[str, list],
    *,
    out_dir: Path,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Write a multi-harness comparison bundle to disk."""
    suffix = (metadata or {}).get("compare_by", "compare")
    run_dir = out_dir / f"{_timestamp_slug()}_{suffix}"
    run_dir.mkdir(parents=True, exist_ok=True)

    arms = list(comparisons.keys())
    task_count = _task_count(next(iter(comparisons.values()))) if comparisons else 0
    manifest = _build_manifest(arms=arms, task_count=task_count, metadata=metadata)
    _write_json(run_dir / "manifest.json", manifest)

    for arm_name, rows in comparisons.items():
        _write_json(run_dir / f"{_arm_filename(arm_name)}.json", [serialize_result_row(row) for row in rows])

    summary = {arm_name: harness_summary(rows) for arm_name, rows in comparisons.items()}
    _write_json(run_dir / "summary.json", summary)
    return run_dir.resolve()


__all__ = [
    "SUMMARY_KEYS",
    "save_compare_run",
    "save_experiment_run",
    "serialize_result_row",
]
