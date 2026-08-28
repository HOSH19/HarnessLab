"""Agent policy tests."""

from langchain_core.messages import HumanMessage

from examples.ticket_triage import nodes
from examples.ticket_triage.rules import AGENT_RULES, OPTIONAL_TOOLS, SYSTEM_PROMPT


def test_system_prompt_matches_agent_rules() -> None:
    """Prompt text is sourced from the shared rules module."""
    assert SYSTEM_PROMPT == AGENT_RULES


def test_agent_rules_cover_sla_and_escalation() -> None:
    """Stress-task policy includes SLA check and escalation branches."""
    rules = AGENT_RULES.lower()
    assert "check_sla" in rules
    assert "escalate_ticket" in rules
    assert "search_kb" in rules


def test_optional_tools_match_escalation_branch() -> None:
    """Optional tools are the SLA/escalation branch only."""
    assert OPTIONAL_TOOLS == frozenset({"check_sla", "escalate_ticket"})


def test_call_model_injects_system_prompt(monkeypatch) -> None:
    """call_model prepends the shared system prompt to task messages."""

    class _FakeLLM:
        def bind_tools(self, _tools):
            return self

        def invoke(self, messages):
            self.messages = messages
            return messages[-1]

    fake = _FakeLLM()
    monkeypatch.setattr(nodes, "_model", lambda: fake)

    nodes.call_model({"messages": [HumanMessage(content="Triage T-011")]})

    assert fake.messages[0].content == AGENT_RULES
