"""Output extraction tests."""

from langchain_core.messages import AIMessage, ToolMessage

from harnesslab.graph.extract import (
    extract_fields_from_messages,
    extract_tool_names_from_messages,
)


def test_extract_fields_from_tool_messages() -> None:
    """Classification and reply are parsed from tool outputs."""
    messages = [
        ToolMessage(
            content='{"ticket_id": "T-001", "category": "account"}',
            name="classify",
            tool_call_id="1",
        ),
        ToolMessage(
            content='{"ticket_id": "T-001", "reply": "Please reset password from settings."}',
            name="draft_reply",
            tool_call_id="2",
        ),
    ]
    fields = extract_fields_from_messages(messages)
    assert fields["classification"] == "account"
    assert "reset password" in fields["final_reply"]


def test_extract_tool_names_from_messages() -> None:
    """Tool names are collected from assistant tool calls."""
    messages = [
        AIMessage(
            content="",
            tool_calls=[
                {"name": "lookup_ticket", "args": {}, "id": "1", "type": "tool_call"},
                {"name": "classify", "args": {}, "id": "2", "type": "tool_call"},
            ],
        ),
        ToolMessage(content="{}", name="lookup_ticket", tool_call_id="1"),
        ToolMessage(content="{}", name="classify", tool_call_id="2"),
    ]
    assert extract_tool_names_from_messages(messages) == [
        "lookup_ticket",
        "classify",
    ]
