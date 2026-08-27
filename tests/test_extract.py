"""Output extraction tests."""

from langchain_core.messages import ToolMessage

from harnesslab.graph.extract import extract_fields_from_messages


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
