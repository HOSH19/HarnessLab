"""Tests for streaming LLM helper used for LangSmith TTFT."""

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage

from harnesslab.graph import llm as llm_mod
from harnesslab.graph.llm import invoke_llm_streaming, mark_first_token_on_trace_root


class _StreamLLM:
    def __init__(self, chunks):
        self.chunks = chunks
        self.streamed = None
        self.config = None

    def stream(self, messages, config=None):
        self.streamed = messages
        self.config = config
        yield from self.chunks

    def invoke(self, messages, config=None):
        raise AssertionError("invoke should not be used when stream succeeds")


class _InvokeOnlyLLM:
    def invoke(self, messages, config=None):
        self.messages = messages
        return AIMessage(content="fallback")


class _FakeRoot:
    def __init__(self):
        self.events: list[dict] = []

    def add_event(self, event):
        self.events.append(event)


def test_invoke_llm_streaming_merges_chunks() -> None:
    """Streamed chunks are merged into one message with full content."""
    llm = _StreamLLM(
        [
            AIMessageChunk(content="Hel"),
            AIMessageChunk(content="lo"),
        ]
    )
    result = invoke_llm_streaming(llm, [HumanMessage(content="hi")], config={"tags": ["t"]})
    assert result.content == "Hello"
    assert llm.streamed[0].content == "hi"
    assert llm.config == {"tags": ["t"]}


def test_invoke_llm_streaming_falls_back_to_invoke() -> None:
    """Models without stream use invoke()."""
    llm = _InvokeOnlyLLM()
    result = invoke_llm_streaming(llm, [HumanMessage(content="hi")])
    assert result.content == "fallback"


def test_mark_first_token_uses_bound_trace_root() -> None:
    """TTFT marker writes new_token onto the evaluate Target run handle."""
    root = _FakeRoot()
    token = llm_mod._trace_root.set(root)
    try:
        mark_first_token_on_trace_root()
        mark_first_token_on_trace_root()  # idempotent
    finally:
        llm_mod._trace_root.reset(token)
    assert len(root.events) == 1
    assert root.events[0]["name"] == "new_token"
    assert "token" in root.events[0]["kwargs"]


def test_bind_trace_root_sets_run_type_llm(monkeypatch) -> None:
    """Experiment TTFT column requires the evaluate root to be typed as llm."""

    class _Root:
        def __init__(self):
            self.run_type = "chain"

    root = _Root()
    monkeypatch.setattr(
        "langsmith.run_helpers.get_current_run_tree",
        lambda: root,
        raising=False,
    )
    # Import path used inside bind_trace_root
    import langsmith.run_helpers as rh

    monkeypatch.setattr(rh, "get_current_run_tree", lambda: root)
    bound = llm_mod.bind_trace_root()
    assert bound is root
    assert root.run_type == "llm"
    llm_mod.clear_trace_root()
