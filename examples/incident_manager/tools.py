"""Tool definitions for the incident manager example agent.

Reads from local JSON fixtures only. Does not call external APIs.
"""

import json
from pathlib import Path

from langchain_core.tools import tool

from examples.incident_manager.flaky import maybe_fail

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "data.json"


def _load_fixtures() -> dict:
    """Load incident fixture data from disk."""
    return json.loads(FIXTURES_PATH.read_text())


@tool
def read_incident(incident_id: str) -> str:
    """Read an incident report by ID.

    Args:
        incident_id: Incident identifier such as I-101.

    Returns:
        JSON string with incident title, summary, and service.
    """
    maybe_fail("read_incident")
    fixtures = _load_fixtures()
    for incident in fixtures["incidents"]:
        if incident["id"] == incident_id:
            return json.dumps(incident)
    return json.dumps({"error": f"Incident {incident_id} not found"})


@tool
def fetch_metrics(incident_id: str) -> str:
    """Fetch live metrics for an incident's affected service.

    Args:
        incident_id: Incident identifier used to look up metrics.

    Returns:
        JSON string with error rates, latency, and status signals.
    """
    maybe_fail("fetch_metrics")
    fixtures = _load_fixtures()
    metrics = fixtures["metrics"].get(incident_id)
    if metrics is None:
        return json.dumps({"error": f"No metrics for incident {incident_id}"})
    return json.dumps({"incident_id": incident_id, **metrics})


@tool
def search_runbooks(query: str) -> str:
    """Search runbooks for remediation guidance matching a query.

    Args:
        query: Search terms from the incident content.

    Returns:
        JSON string with matching runbook summaries.
    """
    maybe_fail("search_runbooks")
    fixtures = _load_fixtures()
    query_lower = query.lower()
    matches = [
        runbook
        for runbook in fixtures["runbooks"]
        if query_lower in runbook["title"].lower() or query_lower in runbook["content"].lower()
    ]
    return json.dumps(matches[:2] if matches else [])


@tool
def correlate_timeline(incident_id: str) -> str:
    """Correlate deployment and alert events on a timeline for an incident.

    Args:
        incident_id: Incident identifier with timeline events.

    Returns:
        JSON string with ordered timeline events.
    """
    maybe_fail("correlate_timeline")
    fixtures = _load_fixtures()
    events = fixtures["timeline"].get(incident_id, [])
    if not events:
        return json.dumps({"incident_id": incident_id, "events": [], "note": "No timeline events"})
    return json.dumps({"incident_id": incident_id, "events": events})


@tool
def classify(category: str, incident_id: str) -> str:
    """Classify an incident into a root-cause category.

    Args:
        category: One of infrastructure, deployment, security, or data_loss.
        incident_id: Incident being classified.

    Returns:
        Confirmation message with assigned category.
    """
    maybe_fail("classify")
    allowed = {"infrastructure", "deployment", "security", "data_loss"}
    if category not in allowed:
        return json.dumps({"error": f"Invalid category. Use one of: {allowed}"})
    return json.dumps({"incident_id": incident_id, "category": category})


@tool
def draft_reply(incident_id: str, reply: str) -> str:
    """Draft an incident update for stakeholders.

    Args:
        incident_id: Incident identifier.
        reply: Draft update text with remediation steps.

    Returns:
        Confirmation with the drafted reply.
    """
    maybe_fail("draft_reply")
    return json.dumps({"incident_id": incident_id, "reply": reply})


TOOLS = [
    read_incident,
    fetch_metrics,
    search_runbooks,
    correlate_timeline,
    classify,
    draft_reply,
]
