"""Load and save harness benchmark baselines."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_baseline(path: Path) -> dict[str, Any]:
    """Load a benchmark baseline JSON file."""
    return json.loads(path.read_text())


def write_baseline(path: Path, payload: dict[str, Any]) -> Path:
    """Write a benchmark baseline JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path.resolve()


def build_baseline(
    *,
    example: str,
    comparisons: dict[str, list],
    summary_keys: list[str],
) -> dict[str, Any]:
    """Build a baseline document from compare results."""
    from harnesslab.report.results import avg_score, task_label, score_for_key

    arms: dict[str, Any] = {}
    for arm_name, rows in comparisons.items():
        arm_payload: dict[str, Any] = {
            key: round(avg_score(rows, key), 4) for key in summary_keys
        }
        per_task: dict[str, dict[str, float]] = {}
        for row in rows:
            label = task_label(row)
            per_task[label] = {
                key: round(score, 4)
                for key in summary_keys
                if (score := score_for_key(row, key)) is not None
            }
        arm_payload["per_task"] = per_task
        arms[arm_name] = arm_payload

    return {"example": example, "arms": arms}
