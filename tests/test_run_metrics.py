"""Run metric helper tests."""

from datetime import datetime, timedelta, timezone

from harnesslab.eval.run_metrics import run_child_count, run_latency_seconds, run_total_tokens


class _FakeRun:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_run_latency_from_start_and_end() -> None:
    """RunTree-style runs derive latency from timestamps."""
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = start + timedelta(seconds=2.5)
    run = _FakeRun(start_time=start, end_time=end)
    assert run_latency_seconds(run) == 2.5


def test_run_total_tokens_reads_extra_usage() -> None:
    """Token counts can live under run.extra usage metadata."""
    run = _FakeRun(extra={"usage_metadata": {"total_tokens": 123}})
    assert run_total_tokens(run) == 123


def test_run_child_count_reads_child_runs() -> None:
    """Child run lists contribute to step counts."""
    run = _FakeRun(child_runs=[object(), object()])
    assert run_child_count(run) == 2
