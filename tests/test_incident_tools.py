"""Incident manager tool tests."""

from examples.incident_manager.flaky import init_flaky_tools
from examples.incident_manager.tools import classify, correlate_timeline, read_incident, search_runbooks


def test_read_incident_returns_fixture() -> None:
    """read_incident loads incident I-101 from fixtures."""
    init_flaky_tools(None)
    payload = read_incident.invoke({"incident_id": "I-101"})
    assert "I-101" in payload
    assert "database" in payload.lower() or "pool" in payload.lower()


def test_classify_validates_categories() -> None:
    """classify rejects unknown categories."""
    init_flaky_tools(None)
    bad = classify.invoke({"category": "network", "incident_id": "I-101"})
    assert "error" in bad.lower()
    good = classify.invoke({"category": "infrastructure", "incident_id": "I-101"})
    assert "infrastructure" in good


def test_correlate_timeline_for_deploy_incident() -> None:
    """I-103 has deploy events on its timeline."""
    init_flaky_tools(None)
    payload = correlate_timeline.invoke({"incident_id": "I-103"})
    assert "v2.14.0" in payload


def test_search_runbooks_finds_security_guidance() -> None:
    """Runbook search returns leaked key remediation."""
    init_flaky_tools(None)
    payload = search_runbooks.invoke({"query": "leaked API key"})
    assert "revoke" in payload.lower()
