"""Research agent tool tests."""

import json

import pytest

from examples.research_agent.flaky import init_flaky_tools
from examples.research_agent.tools import classify, read_source, read_topic, search_literature


def test_read_topic_returns_fixture() -> None:
    """read_topic loads R-001 title and question from fixtures."""
    init_flaky_tools(None)
    payload = json.loads(read_topic.invoke({"topic_id": "R-001"}))
    assert payload["id"] == "R-001"
    assert "transformer" in payload["title"].lower()
    assert "latency" in payload["question"].lower()


def test_read_topic_unknown_id() -> None:
    """read_topic returns an error payload for unknown topics."""
    init_flaky_tools(None)
    payload = json.loads(read_topic.invoke({"topic_id": "R-999"}))
    assert "error" in payload


def test_read_source_returns_ml_fixture() -> None:
    """read_source loads SRC-101 with transformer inference content."""
    init_flaky_tools(None)
    payload = json.loads(read_source.invoke({"source_id": "SRC-101"}))
    assert payload["topic_id"] == "R-001"
    assert "speculative decoding" in payload["abstract"].lower()


def test_classify_validates_categories() -> None:
    """classify rejects unknown categories."""
    init_flaky_tools(None)
    bad = classify.invoke({"category": "finance", "topic_id": "R-001"})
    assert "error" in bad.lower()
    good = classify.invoke({"category": "ml", "topic_id": "R-001"})
    assert "ml" in good


def test_search_literature_flaky_integration() -> None:
    """search_literature raises once then succeeds when flaky_tools requests one failure."""
    init_flaky_tools({"search_literature": 1})

    with pytest.raises(RuntimeError, match="search_literature"):
        search_literature.invoke({"query": "transformer"})

    result = json.loads(search_literature.invoke({"query": "consensus"}))
    assert result
