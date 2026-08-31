"""Circuit breaker middleware tests."""

import pytest

from harnesslab.middleware.circuit_breaker import (
    CircuitOpenError,
    is_circuit_open,
    record_tool_failure,
    record_tool_success,
)
from harnesslab.middleware.runtime import init_run_context


def test_circuit_opens_after_threshold_failures() -> None:
    """Circuit opens once consecutive failures reach the threshold."""
    context = init_run_context()
    record_tool_failure("fetch_metrics", context, threshold=2)
    assert not is_circuit_open("fetch_metrics", context)
    record_tool_failure("fetch_metrics", context, threshold=2)
    assert is_circuit_open("fetch_metrics", context)


def test_success_resets_circuit_failures() -> None:
    """A successful call clears failure counts and re-closes the circuit."""
    context = init_run_context()
    record_tool_failure("fetch_metrics", context, threshold=2)
    record_tool_success("fetch_metrics", context)
    record_tool_failure("fetch_metrics", context, threshold=2)
    assert not is_circuit_open("fetch_metrics", context)


def test_circuit_open_error_message() -> None:
    """CircuitOpenError includes the tool name."""
    error = CircuitOpenError("search_runbooks")
    assert error.tool_name == "search_runbooks"
