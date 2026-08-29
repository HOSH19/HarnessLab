"""Simulated flaky tool failures for the incident analyst example."""

from harnesslab.flaky import attempt_count, init_flaky_tools, maybe_fail

__all__ = ["attempt_count", "init_flaky_tools", "maybe_fail"]
