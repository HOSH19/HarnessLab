"""Tool sequence evaluator tests."""

from harnesslab.eval.tool_sequence import tool_sequence


class _FakeRun:
    def __init__(self, outputs):
        self.outputs = outputs


class _FakeExample:
    def __init__(self, outputs):
        self.outputs = outputs


def test_tool_sequence_passes_without_expected_tools() -> None:
    """Missing expected_tools yields a neutral pass."""
    run = _FakeRun({"graph_trajectory": {"results": []}})
    example = _FakeExample({"expected_nodes": ["agent"]})
    result = tool_sequence(run, example)
    assert result["score"] == 1.0
    assert result["comment"] == "no expected_tools"


def test_tool_sequence_matches_expected_subsequence() -> None:
    """Expected tools must appear in order within actual tool calls."""
    run = _FakeRun(
        {
            "graph_trajectory": {
                "results": [
                    {
                        "messages": [
                            {
                                "role": "assistant",
                                "tool_calls": [
                                    {"function": {"name": "lookup_ticket"}},
                                    {"function": {"name": "classify"}},
                                ],
                            },
                            {"role": "tool", "name": "lookup_ticket"},
                            {"role": "tool", "name": "classify"},
                            {
                                "role": "assistant",
                                "tool_calls": [{"function": {"name": "draft_reply"}}],
                            },
                            {"role": "tool", "name": "draft_reply"},
                        ]
                    }
                ]
            }
        }
    )
    example = _FakeExample({"expected_tools": ["lookup_ticket", "classify", "draft_reply"]})
    result = tool_sequence(run, example)
    assert result["score"] == 1.0


def test_tool_sequence_partial_credit_for_missing_tail() -> None:
    """Missing trailing tools receive proportional partial credit."""
    run = _FakeRun(
        {
            "graph_trajectory": {
                "results": [
                    {
                        "messages": [
                            {
                                "role": "assistant",
                                "tool_calls": [
                                    {"function": {"name": "read_ticket"}},
                                    {"function": {"name": "search_kb"}},
                                ],
                            },
                            {"role": "tool", "name": "read_ticket"},
                            {"role": "tool", "name": "search_kb"},
                        ]
                    }
                ]
            }
        }
    )
    example = _FakeExample({"expected_tools": ["read_ticket", "search_kb", "classify", "draft_reply"]})
    result = tool_sequence(run, example)
    assert result["score"] == 0.5


def test_tool_sequence_fails_on_wrong_order() -> None:
    """Out-of-order tool calls fail the subsequence check."""
    run = _FakeRun(
        {
            "graph_trajectory": {
                "results": [
                    {
                        "messages": [
                            {
                                "role": "assistant",
                                "tool_calls": [{"function": {"name": "classify"}}],
                            },
                            {"role": "tool", "name": "classify"},
                        ]
                    }
                ]
            }
        }
    )
    example = _FakeExample({"expected_tools": ["lookup_ticket", "classify"]})
    result = tool_sequence(run, example)
    assert result["score"] == 0.0
