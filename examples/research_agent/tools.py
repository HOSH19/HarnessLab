"""Tool definitions for the research agent example."""

import json
from pathlib import Path

from langchain_core.tools import tool

from examples.research_agent.flaky import maybe_fail

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "data.json"


def _load_fixtures() -> dict:
    """Load research fixture data from disk."""
    return json.loads(FIXTURES_PATH.read_text())


@tool
def read_topic(topic_id: str) -> str:
    """Read a research topic by ID.

    Args:
        topic_id: Topic identifier such as R-001.

    Returns:
        JSON string with topic title and research question.
    """
    maybe_fail("read_topic")
    fixtures = _load_fixtures()
    for topic in fixtures["topics"]:
        if topic["id"] == topic_id:
            return json.dumps(topic)
    return json.dumps({"error": f"Topic {topic_id} not found"})


@tool
def search_literature(query: str) -> str:
    """Search indexed papers and memos matching a query.

    Args:
        query: Search terms from the research topic.

    Returns:
        JSON string with matching literature snippets.
    """
    maybe_fail("search_literature")
    fixtures = _load_fixtures()
    query_lower = query.lower()
    matches = [
        item
        for item in fixtures["literature"]
        if query_lower in item["title"].lower() or query_lower in item["snippet"].lower()
    ]
    return json.dumps(matches[:2] if matches else [])


@tool
def read_source(source_id: str) -> str:
    """Read a source abstract by ID.

    Args:
        source_id: Source identifier such as SRC-101.

    Returns:
        JSON string with title and abstract.
    """
    maybe_fail("read_source")
    fixtures = _load_fixtures()
    for source in fixtures["sources"]:
        if source["id"] == source_id:
            return json.dumps(source)
    return json.dumps({"error": f"Source {source_id} not found"})


@tool
def classify(category: str, topic_id: str) -> str:
    """Classify a research topic into a domain.

    Args:
        category: One of ml, systems, security, or product.
        topic_id: Topic identifier such as R-001.

    Returns:
        Confirmation message with assigned category.
    """
    maybe_fail("classify")
    allowed = {"ml", "systems", "security", "product"}
    if category not in allowed:
        return json.dumps({"error": f"Invalid category. Use one of: {allowed}"})
    return json.dumps({"topic_id": topic_id, "category": category})


@tool
def draft_reply(topic_id: str, reply: str) -> str:
    """Draft a research summary for stakeholders.

    Args:
        topic_id: Topic identifier.
        reply: Summary text with key findings.

    Returns:
        Confirmation with the drafted reply.
    """
    maybe_fail("draft_reply")
    return json.dumps({"topic_id": topic_id, "reply": reply})


TOOLS = [read_topic, search_literature, read_source, classify, draft_reply]
