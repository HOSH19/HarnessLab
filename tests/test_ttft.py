"""Tests for ttft_seconds feedback evaluator."""

from datetime import datetime, timezone
from types import SimpleNamespace

from harnesslab.eval.ttft import ttft_from_run, ttft_seconds
from harnesslab.graph import llm as llm_mod


def test_ttft_from_outputs_details() -> None:
    """Stored details.ttft_seconds wins over run timing fields."""
    run = SimpleNamespace(
        outputs={"details": {"ttft_seconds": 1.25}},
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        first_token_time=None,
        events=[],
    )
    assert ttft_from_run(run) == 1.25


def test_ttft_from_first_token_time() -> None:
    """Compute seconds from start_time and first_token_time."""
    start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    first = datetime(2026, 1, 1, 0, 0, 2, 500000, tzinfo=timezone.utc)
    run = SimpleNamespace(outputs={}, start_time=start, first_token_time=first, events=[])
    assert ttft_from_run(run) == 2.5


def test_ttft_evaluator_unavailable() -> None:
    """Missing timing yields score 0 with an unavailable comment."""
    run = SimpleNamespace(outputs={}, start_time=None, first_token_time=None, events=[])
    result = ttft_seconds(run, SimpleNamespace(outputs={}))
    assert result["key"] == "ttft_seconds"
    assert result["score"] == 0.0
    assert "unavailable" in result["comment"]


def test_measured_ttft_seconds_uses_bound_times() -> None:
    """ContextVar start + first-token mark produce a measured TTFT."""

    class _Root:
        events: list = []

        def add_event(self, event):
            self.events.append(event)

    root = _Root()
    start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    token_root = llm_mod._trace_root.set(root)
    token_start = llm_mod._run_started_at.set(start)
    token_ft = llm_mod._first_token_at.set(None)
    try:
        llm_mod.mark_first_token_on_trace_root()
        value = llm_mod.measured_ttft_seconds()
    finally:
        llm_mod._trace_root.reset(token_root)
        llm_mod._run_started_at.reset(token_start)
        llm_mod._first_token_at.reset(token_ft)
    assert value is not None and value >= 0.0
    assert root.events[0]["name"] == "new_token"
