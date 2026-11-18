"""Time-to-first-token feedback for LangSmith experiment tables.

The native experiment **Time to First Token** column stays blank for agent
``evaluate`` Targets even when ``first_token_time`` is set on the run. Publish
``ttft_seconds`` as feedback so a numeric cell always appears.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from langsmith.schemas import Example, Run

from harnesslab.eval.outputs import run_output_field


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _parse_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return _aware(value)
    if isinstance(value, str) and value:
        text = value.replace("Z", "+00:00")
        try:
            return _aware(datetime.fromisoformat(text))
        except ValueError:
            return None
    return None


def ttft_from_run(run: Any) -> float | None:
    """Return TTFT seconds from outputs, first_token_time, or new_token events."""
    outputs = getattr(run, "outputs", None) or {}
    if isinstance(outputs, dict):
        stored = run_output_field(outputs, "ttft_seconds")
        if stored is not None:
            return float(stored)

    start = _aware(getattr(run, "start_time", None))
    first = _aware(getattr(run, "first_token_time", None))
    if start is None or first is None:
        for event in getattr(run, "events", None) or []:
            if isinstance(event, dict) and event.get("name") == "new_token":
                first = _parse_time(event.get("time"))
                break
    if start is None or first is None:
        return None
    return max(0.0, round((first - start).total_seconds(), 3))


def ttft_seconds(run: Run, example: Example) -> dict:
    """Score wall-clock seconds from Target start to first streamed token."""
    _ = example
    value = ttft_from_run(run)
    if value is None:
        return {
            "key": "ttft_seconds",
            "score": 0.0,
            "comment": "ttft_unavailable",
        }
    return {
        "key": "ttft_seconds",
        "score": value,
        "comment": f"ttft_seconds={value:.3f}",
    }
