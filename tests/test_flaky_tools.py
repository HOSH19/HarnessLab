"""Flaky tool wrapper tests."""

import json
import pytest

from examples.ticket_triage.flaky import attempt_count, init_flaky_tools, maybe_fail
from examples.ticket_triage.tools import read_ticket, search_kb


def test_maybe_fail_raises_then_succeeds() -> None:
    """Tool fails N times with exceptions then succeeds on the next call."""
    init_flaky_tools({"read_ticket": 2})

    with pytest.raises(RuntimeError, match="read_ticket"):
        maybe_fail("read_ticket")
    assert attempt_count("read_ticket") == 1

    with pytest.raises(RuntimeError, match="read_ticket"):
        maybe_fail("read_ticket")
    assert attempt_count("read_ticket") == 2

    maybe_fail("read_ticket")
    assert attempt_count("read_ticket") == 3


def test_unconfigured_tool_never_fails() -> None:
    """Tools without flaky config always succeed."""
    init_flaky_tools({"read_ticket": 1})
    maybe_fail("search_kb")
    assert attempt_count("search_kb") == 0


def test_read_ticket_flaky_integration() -> None:
    """read_ticket raises on first attempt when flaky_tools requests one failure."""
    init_flaky_tools({"read_ticket": 1})

    with pytest.raises(RuntimeError, match="read_ticket"):
        read_ticket.invoke({"ticket_id": "T-011"})

    result = json.loads(read_ticket.invoke({"ticket_id": "T-011"}))
    assert result["id"] == "T-011"


def test_flaky_reset_between_runs() -> None:
    """init_flaky_tools clears attempt counts for a new run."""
    init_flaky_tools({"search_kb": 1})
    with pytest.raises(RuntimeError):
        search_kb.invoke({"query": "billing"})
    assert attempt_count("search_kb") == 1

    init_flaky_tools(None)
    search_kb.invoke({"query": "billing"})
    assert attempt_count("search_kb") == 0
