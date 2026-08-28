"""Ticket triage tool tests."""

import json

import pytest

from examples.ticket_triage.flaky import init_flaky_tools
from examples.ticket_triage.tools import check_sla, escalate_ticket, search_kb


def test_check_sla_returns_fixture_data() -> None:
    """check_sla reads SLA tier and deadline from ticket fixtures."""
    result = json.loads(check_sla.invoke({"ticket_id": "T-016"}))
    assert result["sla_tier"] == "priority"
    assert result["deadline_hours"] == 4


def test_check_sla_defaults_for_standard_tickets() -> None:
    """Tickets without SLA fields get standard defaults."""
    result = json.loads(check_sla.invoke({"ticket_id": "T-001"}))
    assert result["sla_tier"] == "standard"
    assert result["deadline_hours"] == 48


def test_escalate_ticket_returns_confirmation() -> None:
    """escalate_ticket records escalation reason."""
    result = json.loads(
        escalate_ticket.invoke({"ticket_id": "T-016", "reason": "priority outage"})
    )
    assert result["escalated"] is True
    assert result["reason"] == "priority outage"


def test_search_kb_flaky_integration() -> None:
    """search_kb raises twice then succeeds when flaky_tools requests two failures."""
    init_flaky_tools({"search_kb": 2})

    with pytest.raises(RuntimeError, match="search_kb"):
        search_kb.invoke({"query": "ssl"})
    with pytest.raises(RuntimeError, match="search_kb"):
        search_kb.invoke({"query": "ssl"})

    result = json.loads(search_kb.invoke({"query": "ssl certificate"}))
    assert result
    assert "SSL" in result[0]["title"]
