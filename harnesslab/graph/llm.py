"""Stream LLM calls for LangSmith TTFT; return a merged full message."""

from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# Evaluate Target RunTree — LangChain tracers omit parent_run, so we bind it here.
_trace_root: ContextVar[Any] = ContextVar("harnesslab_trace_root", default=None)
_run_started_at: ContextVar[datetime | None] = ContextVar(
    "harnesslab_run_started_at", default=None
)
_first_token_at: ContextVar[datetime | None] = ContextVar(
    "harnesslab_first_token_at", default=None
)


def bind_trace_root() -> Any | None:
    """Bind the current evaluate Target run for first-token marking."""
    started = datetime.now(timezone.utc)
    _run_started_at.set(started)
    _first_token_at.set(None)
    try:
        from langsmith.run_helpers import get_current_run_tree

        root = get_current_run_tree()
    except Exception:
        root = None

    if root is not None:
        try:
            root.run_type = "llm"  # safety if evaluate retargeted the root
        except AttributeError:
            pass
        start = getattr(root, "start_time", None)
        if isinstance(start, datetime):
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            _run_started_at.set(start)

    _trace_root.set(root)
    return root


def clear_trace_root() -> None:
    """Clear the bound evaluate-root run handle."""
    _trace_root.set(None)
    _run_started_at.set(None)
    _first_token_at.set(None)


def measured_ttft_seconds() -> float | None:
    """Return Target-start → first-token seconds when both times are known."""
    start = _run_started_at.get()
    first = _first_token_at.get()
    if start is None or first is None:
        return None
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if first.tzinfo is None:
        first = first.replace(tzinfo=timezone.utc)
    return max(0.0, round((first - start).total_seconds(), 3))


def mark_first_token_on_trace_root() -> None:
    """Emit a once-per-run root ``new_token`` event (LangSmith first_token_time)."""
    if _first_token_at.get() is not None:
        return
    now = datetime.now(timezone.utc)
    _first_token_at.set(now)
    root = _trace_root.get()
    if root is None or not hasattr(root, "add_event"):
        return
    events = getattr(root, "events", None) or []
    if any(isinstance(e, dict) and e.get("name") == "new_token" for e in events):
        return
    root.add_event(
        {
            "name": "new_token",
            "time": now.isoformat(),
            "kwargs": {"token": ""},
        }
    )


def invoke_llm_streaming(llm: Any, messages: list, config: Any | None = None) -> Any:
    """Stream an LLM call, mark TTFT on first chunk, merge into one message."""
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
