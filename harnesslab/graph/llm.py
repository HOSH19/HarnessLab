"""LLM helpers that stream tokens for LangSmith TTFT while returning full messages."""

from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# Bound at evaluate Target entry — LangChain tracers do not set RunTree.parent_run,
# so walking parents during stream cannot reach the experiment row.
_trace_root: ContextVar[Any] = ContextVar("harnesslab_trace_root", default=None)


def bind_trace_root() -> Any | None:
    """Capture the current LangSmith run (evaluate Target) for TTFT marking.

    LangSmith's experiment-table **Time to First Token** column only renders for
    roots with ``run_type="llm"`` (see run data format). Evaluate wraps agent
    targets as ``chain``, so we retarget the root type when binding.
    """
    try:
        from langsmith.run_helpers import get_current_run_tree
    except Exception:
        _trace_root.set(None)
        return None

    try:
        root = get_current_run_tree()
    except Exception:
        root = None

    if root is not None:
        try:
            root.run_type = "llm"
        except Exception:
            pass

    _trace_root.set(root)
    return root


def clear_trace_root() -> None:
    """Drop the bound evaluate-root run handle."""
    _trace_root.set(None)


def mark_first_token_on_trace_root() -> None:
    """Emit a root-level new_token event so LangSmith derives first_token_time."""
    root = _trace_root.get()
    if root is None:
        return
    try:
        events = getattr(root, "events", None) or []
        if any(isinstance(event, dict) and event.get("name") == "new_token" for event in events):
            return
        # Match the ingest shape LangSmith documents for TTFT (kwargs.token required
        # for some ingest paths; naive UTC timestamp matches ChatOpenAI tracers).
        token_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")
        root.add_event(
            {
                "name": "new_token",
                "time": token_time,
                "kwargs": {"token": [""]},
            }
        )
        if getattr(root, "run_type", None) != "llm":
            root.run_type = "llm"
    except Exception:
        return

def invoke_llm_streaming(llm: Any, messages: list, config: Any | None = None) -> Any:
    """Stream an LLM call and merge chunks into one complete message.

    LangSmith records time-to-first-token from ``new_token`` events, which only
    fire when the model is actually streamed (not ``invoke``). Pass LangGraph
    ``config`` so callbacks/tracing stay attached to the active run tree.
    """
    stream = getattr(llm, "stream", None)
    if stream is None:
        if config is None:
            return llm.invoke(messages)
        return llm.invoke(messages, config=config)

    chunks: list[Any] = []
    marked = False
    iterator = stream(messages) if config is None else stream(messages, config=config)
    for chunk in iterator:
        if not marked:
            mark_first_token_on_trace_root()
            marked = True
        chunks.append(chunk)

    if not chunks:
        invoke = getattr(llm, "invoke", None)
        if invoke is None:
            raise RuntimeError("LLM returned no stream chunks and has no invoke()")
        if config is None:
            return invoke(messages)
        return invoke(messages, config=config)

    merged = chunks[0]
    for chunk in chunks[1:]:
        merged = merged + chunk
    return merged
