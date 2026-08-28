"""Output extraction tests."""

from langchain_core.messages import AIMessage, ToolMessage

from harnesslab.graph.extract import (
    extract_fields_from_messages,
    extract_tool_names_from_messages,
    extract_tool_names_from_outputs,
    extract_tool_names_from_trajectory,
    format_display_output,
)


def test_format_display_output_matches_reference_category() -> None:
    """Outputs column shows classification to align with reference expected_category."""
    assert format_display_output("technical", "Escalated outage") == "technical"
    assert format_display_output("", "Refund processed") == ""
    assert format_display_output("billing", "long reply text") == "billing"


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
    """Tool names are collected from assistant and tool messages."""
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


def test_extract_tool_names_from_trajectory() -> None:
    """Trajectory result messages expose tool names in OpenAI format."""
    trajectory = {
        "results": [
            {
                "messages": [
                    {
                        "role": "assistant",
                        "tool_calls": [{"function": {"name": "draft_reply"}}],
                    },
                    {"role": "tool", "name": "draft_reply"},
                ]
            }
        ]
    }
    assert extract_tool_names_from_trajectory(trajectory) == ["draft_reply"]


def test_extract_tool_names_from_outputs_prefers_messages() -> None:
    """Direct messages in outputs take precedence over trajectory data."""
    outputs = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "classify", "args": {}, "id": "1", "type": "tool_call"},
                ],
            )
        ],
        "graph_trajectory": {"results": []},
    }
    assert extract_tool_names_from_outputs(outputs) == ["classify"]


def test_extract_tool_names_from_outputs_uses_tool_names() -> None:
    """Serialized tool_names list is used when messages are omitted."""
    outputs = {
        "tool_names": ["read_ticket", "classify", "draft_reply"],
        "graph_trajectory": {"results": []},
    }
    assert extract_tool_names_from_outputs(outputs) == [
        "read_ticket",
        "classify",
        "draft_reply",
    ]
