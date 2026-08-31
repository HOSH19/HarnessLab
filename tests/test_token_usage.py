"""Token usage helper tests."""

from langchain_core.messages import AIMessage

from harnesslab.eval.token_usage import aggregate_usage_metadata, message_tokens, usage_dict_total_tokens


def test_usage_dict_total_tokens_prefers_total_field() -> None:
    """total_tokens is used when present on usage metadata."""
    usage = {"input_tokens": 10, "output_tokens": 5, "total_tokens": 99}
    assert usage_dict_total_tokens(usage) == 99


def test_usage_dict_total_tokens_sums_input_output() -> None:
    """Input and output tokens are summed when total_tokens is absent."""
    usage = {"input_tokens": 12, "output_tokens": 8}
    assert usage_dict_total_tokens(usage) == 20


def test_aggregate_usage_metadata_sums_models() -> None:
    """Callback usage metadata is aggregated across models."""
    usage = {
        "gpt-4.1-nano": {"total_tokens": 100},
        "gpt-4.1-mini": {"total_tokens": 50},
    }
    total, model = aggregate_usage_metadata(usage)
    assert total == 150
    assert model == "gpt-4.1-nano"


def test_message_tokens_sums_ai_messages() -> None:
    """AIMessage usage metadata contributes to message token totals."""
    messages = [
        AIMessage(content="a", usage_metadata={"input_tokens": 20, "output_tokens": 10, "total_tokens": 30}),
        AIMessage(
            content="b",
            usage_metadata={"input_tokens": 4, "output_tokens": 6, "total_tokens": 10},
        ),
    ]
    assert message_tokens(messages) == 40