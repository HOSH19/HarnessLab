"""Pipeline routing tests."""

from langchain_core.messages import AIMessage, HumanMessage

from harnesslab.graph.pipeline import (
    NUDGE_MESSAGE,
    already_nudged,
    nudge_incomplete_pipeline,
    pipeline_complete,
    should_continue_with_nudge,
)


def test_pipeline_complete_requires_classify_and_draft_reply() -> None:
    """Pipeline is incomplete until both required tools were called."""
    messages = [
        AIMessage(content="", tool_calls=[{"name": "read_ticket", "args": {}, "id": "1"}]),
    ]
    assert pipeline_complete(messages) is False

    messages.append(
        AIMessage(
            content="",
            tool_calls=[
                {"name": "classify", "args": {}, "id": "2"},
                {"name": "draft_reply", "args": {}, "id": "3"},
            ],
        )
    )
    assert pipeline_complete(messages) is True


def test_should_continue_with_nudge_before_pipeline_complete() -> None:
    """Incomplete pipelines route to nudge instead of ending."""
    state = {
        "messages": [AIMessage(content="I will help with your refund.")],
    }
    assert should_continue_with_nudge(state) == "nudge"


def test_should_continue_with_nudge_only_once() -> None:
    """After nudging once, the graph is allowed to end even if still incomplete."""
    state = {
        "messages": [
            AIMessage(content="Still working on it."),
            HumanMessage(content=NUDGE_MESSAGE),
            AIMessage(content="Okay."),
        ],
    }
    assert already_nudged(state["messages"]) is True
    assert should_continue_with_nudge(state) == "end"


def test_nudge_incomplete_pipeline_injects_reminder() -> None:
    """Nudge node appends the required-tools reminder."""
    update = nudge_incomplete_pipeline({"messages": []})
    assert update["messages"][0].content == NUDGE_MESSAGE
