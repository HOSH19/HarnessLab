"""Tests for streaming LLM helper and LangSmith TTFT marking."""

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
    llm = _InvokeOnlyLLM()
    result = invoke_llm_streaming(llm, [HumanMessage(content="hi")])
    assert result.content == "fallback"


def test_mark_first_token_uses_bound_trace_root() -> None:
    root = _FakeRoot()
    token = llm_mod._trace_root.set(root)
    token_ft = llm_mod._first_token_at.set(None)
    try:
        mark_first_token_on_trace_root()
        mark_first_token_on_trace_root()  # idempotent
    finally:
        llm_mod._trace_root.reset(token)
        llm_mod._first_token_at.reset(token_ft)
    assert len(root.events) == 1
    assert root.events[0]["name"] == "new_token"
    assert "token" in root.events[0]["kwargs"]
    assert "T" in root.events[0]["time"]


def test_make_target_is_prewrapped_as_llm() -> None:
    from langsmith.evaluation._runner import _ensure_traceable
    from langsmith.run_helpers import is_traceable_function

    from harnesslab.config.models import HarnessConfig
    from harnesslab.experiments.target import make_target

    harness = HarnessConfig(name="minimal")
    target = make_target(lambda *_args, **_kwargs: object(), harness)
    assert is_traceable_function(target)
    freevars = target.__code__.co_freevars
    cells = target.__closure__
    assert freevars and cells
    container = dict(zip(freevars, (c.cell_contents for c in cells))).get("container_input")
    assert isinstance(container, dict)
    assert container.get("run_type") == "llm"
    assert _ensure_traceable(target) is target
