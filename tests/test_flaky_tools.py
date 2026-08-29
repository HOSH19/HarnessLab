"""Flaky tool simulation tests."""

import json

import pytest

from examples.research_agent.flaky import attempt_count, init_flaky_tools, maybe_fail
from examples.research_agent.tools import read_source, search_literature


def test_maybe_fail_raises_until_budget_exhausted() -> None:
    """maybe_fail raises for the configured number of attempts."""
    init_flaky_tools({"read_source": 2})

    with pytest.raises(RuntimeError, match="read_source"):
        maybe_fail("read_source")
    assert attempt_count("read_source") == 1

    with pytest.raises(RuntimeError, match="read_source"):
        maybe_fail("read_source")
    assert attempt_count("read_source") == 2

    maybe_fail("read_source")
    assert attempt_count("read_source") == 3


def test_maybe_fail_noop_without_config() -> None:
    """maybe_fail is a no-op when flaky_tools is unset."""
    init_flaky_tools(None)
    maybe_fail("read_source")


def test_read_source_flaky_integration() -> None:
    """read_source raises on first attempt when flaky_tools requests one failure."""
    init_flaky_tools({"read_source": 1})

    with pytest.raises(RuntimeError, match="read_source"):
        read_source.invoke({"source_id": "SRC-101"})

    result = json.loads(read_source.invoke({"source_id": "SRC-101"}))
    assert result["id"] == "SRC-101"


def test_search_literature_flaky_integration() -> None:
    """search_literature raises twice then succeeds when flaky_tools requests two failures."""
    init_flaky_tools({"search_literature": 2})

    with pytest.raises(RuntimeError, match="search_literature"):
        search_literature.invoke({"query": "raft"})
    with pytest.raises(RuntimeError, match="search_literature"):
        search_literature.invoke({"query": "raft"})

    result = json.loads(search_literature.invoke({"query": "consensus"}))
    assert result
