"""CLI helper tests."""

from harnesslab.cli.main import _apply_smoke_limits


def test_smoke_limits_harness_compare_to_two_arms_and_tasks() -> None:
    """Smoke mode caps harness compare to minimal/retry and two tasks."""
    harness, tasks, task = _apply_smoke_limits(
        smoke=True,
        compare_by="harness",
        harness="minimal,retry,trim",
        tasks=None,
        task=None,
    )
    assert harness == "minimal,retry"
    assert tasks == 2
    assert task is None


def test_smoke_respects_explicit_task_filter() -> None:
    """A single --task filter is already minimal and should not be overridden."""
    harness, tasks, task = _apply_smoke_limits(
        smoke=True,
        compare_by="harness",
        harness="minimal,retry,trim",
        tasks=None,
        task="T-011",
    )
    assert harness == "minimal,retry,trim"
    assert tasks is None
    assert task == "T-011"
