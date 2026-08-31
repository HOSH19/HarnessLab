"""Target output tests for local token tracking."""

from contextlib import contextmanager
from unittest.mock import MagicMock

from langchain_core.callbacks.usage import UsageMetadataCallbackHandler

from harnesslab.experiments import target as target_module
from harnesslab.experiments.target import extract_outputs, make_target


def test_extract_outputs_includes_token_fields() -> None:
    """extract_outputs attaches token and model fields for evaluators."""
    graph = MagicMock()
    config = {"configurable": {"thread_id": "t1"}}
    outputs = extract_outputs(
        {"messages": [], "error_count": 0},
        graph,
        config,
        total_tokens=250,
        model="gpt-4.1-nano",
        usage_metadata={"gpt-4.1-nano": {"total_tokens": 250}},
    )
    assert "model" not in outputs
    assert "total_tokens" not in outputs
    assert "usage_metadata" not in outputs
    assert outputs["details"]["model"] == "gpt-4.1-nano"
    assert outputs["details"]["total_tokens"] == 250
    assert outputs["details"]["usage_metadata"]["gpt-4.1-nano"]["total_tokens"] == 250


def test_make_target_attaches_usage_from_callback(monkeypatch) -> None:
    """make_target records callback usage metadata on returned outputs."""
    graph = MagicMock()
    graph.invoke.return_value = {"messages": [], "error_count": 0}

    @contextmanager
    def fake_usage_callback():
        callback = UsageMetadataCallbackHandler()
        callback.usage_metadata = {"gpt-4.1-nano": {"total_tokens": 321}}
        yield callback

    monkeypatch.setattr(target_module, "get_usage_metadata_callback", fake_usage_callback)

    harness = MagicMock()
    harness.observability.langsmith_project = "test"
    harness.observability.trace_metadata = {}
    harness.name = "minimal"
    harness.execution = MagicMock()

    target = make_target(lambda _: graph, harness)
    outputs = target({"prompt": "hello", "ticket_id": "T-1"})

    assert outputs["details"]["total_tokens"] == 321
    assert outputs["details"]["model"] == "gpt-4.1-nano"
    assert "model" not in outputs
    run_config = graph.invoke.call_args.kwargs["config"]
    assert run_config["callbacks"]
