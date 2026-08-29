"""Agent policy tests."""

from langchain_core.messages import HumanMessage

from examples.research_agent import nodes
from examples.research_agent.rules import AGENT_RULES, OPTIONAL_TOOLS, SYSTEM_PROMPT


def test_system_prompt_matches_agent_rules() -> None:
    """Prompt text is sourced from the shared rules module."""
    assert SYSTEM_PROMPT == AGENT_RULES


def test_agent_rules_cover_research_workflow() -> None:
    """Research workflow includes search, read, classify, and draft_reply."""
    rules = AGENT_RULES.lower()
    assert "search_literature" in rules
    assert "read_source" in rules
    assert "classify" in rules
    assert "draft_reply" in rules
    assert "must call classify" in rules


def test_optional_tools_empty_for_research_agent() -> None:
    """Research agent has no optional tool branch."""
    assert OPTIONAL_TOOLS == frozenset()


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

    nodes.call_model({"messages": [HumanMessage(content="Research R-001")]})

    assert fake.messages[0].content == AGENT_RULES
