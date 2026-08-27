"""Tool definitions for the ticket triage example agent.

Reads from local JSON fixtures only. Does not call external APIs.
"""

import json
from pathlib import Path

from langchain_core.tools import tool

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "data.json"


def _load_fixtures() -> dict:
    """Load ticket and KB fixture data from disk."""
    return json.loads(FIXTURES_PATH.read_text())


@tool
def read_ticket(ticket_id: str) -> str:
    """Read a support ticket by ID.

    Args:
        ticket_id: Ticket identifier such as T-001.

    Returns:
        JSON string with ticket subject and body.
    """
    fixtures = _load_fixtures()
    for ticket in fixtures["tickets"]:
        if ticket["id"] == ticket_id:
            return json.dumps(ticket)
    return json.dumps({"error": f"Ticket {ticket_id} not found"})


@tool
def search_kb(query: str) -> str:
    """Search the knowledge base for articles matching a query.

    Args:
        query: Search terms from the ticket content.

    Returns:
        JSON string with matching KB article summaries.
    """
    fixtures = _load_fixtures()
    query_lower = query.lower()
    matches = [
        article
        for article in fixtures["kb"]
        if query_lower in article["title"].lower() or query_lower in article["content"].lower()
    ]
    return json.dumps(matches[:2] if matches else [])


@tool
def classify(category: str, ticket_id: str) -> str:
    """Classify a ticket into a support category.

    Args:
        category: One of account, billing, or technical.
        ticket_id: Ticket being classified.

    Returns:
        Confirmation message with assigned category.
    """
    allowed = {"account", "billing", "technical"}
    if category not in allowed:
        return json.dumps({"error": f"Invalid category. Use one of: {allowed}"})
    return json.dumps({"ticket_id": ticket_id, "category": category})


@tool
def draft_reply(ticket_id: str, reply: str) -> str:
    """Draft a customer reply for a triaged ticket.

    Args:
        ticket_id: Ticket identifier.
        reply: Draft reply text for the customer.

    Returns:
        Confirmation with the drafted reply.
    """
    return json.dumps({"ticket_id": ticket_id, "reply": reply})


TOOLS = [read_ticket, search_kb, classify, draft_reply]
