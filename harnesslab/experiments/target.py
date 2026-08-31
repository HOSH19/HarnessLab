"""LangSmith target functions for harness experiment runs."""

import os
import uuid
from collections.abc import Callable
from typing import Any

from agentevals.graph_trajectory.utils import extract_langgraph_trajectory_from_thread
from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.messages import AIMessage, HumanMessage

from harnesslab.config.model_catalog import DEFAULT_MODEL
from harnesslab.eval.token_usage import aggregate_usage_metadata, message_tokens
from harnesslab.config.models import HarnessConfig
from harnesslab.flaky import init_flaky_tools
from harnesslab.graph.extract import extract_fields_from_messages
from harnesslab.middleware.limits import recursion_limit as graph_recursion_limit
from harnesslab.middleware.runtime import clear_run_context, init_run_context


def build_initial_messages(prompt: str, conversation_history: list[dict] | None) -> list:
    """Build message list from optional prior turns plus the task prompt."""
    messages: list = []
    for turn in conversation_history or []:
        role = turn.get("role", "human")
        content = turn.get("content", "")
        if role in {"human", "user"}:
            messages.append(HumanMessage(content=content))
        elif role in {"ai", "assistant"}:
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=prompt))
    return messages


def invoke_config(harness: HarnessConfig) -> dict:
    """Build LangGraph invoke config with recursion limit and trace tags."""
    project = harness.observability.langsmith_project or "harnesslab"
    os.environ["LANGSMITH_PROJECT"] = project

    configurable: dict[str, Any] = {
        "thread_id": str(uuid.uuid4()),
        "harness_name": harness.name,
        **harness.observability.trace_metadata,
    }

    return {
        "configurable": configurable,
        "recursion_limit": graph_recursion_limit(harness.execution),
    }


def extract_outputs(
    state: dict,
    graph: Any,
    config: dict,
    *,
    total_tokens: int = 0,
    model: str | None = None,
    usage_metadata: dict | None = None,
) -> dict:
    """Pull evaluation fields from graph state and trajectory."""
    messages = state.get("messages", [])
    parsed = extract_fields_from_messages(messages)
    trajectory = extract_langgraph_trajectory_from_thread(graph, config)
    classification = parsed["classification"] or state.get("classification", "")
    final_reply = parsed["final_reply"] or state.get("final_reply", "")

    outputs: dict[str, Any] = {
        "output": classification or "",
        "classification": classification or "",
        "error_count": state.get("error_count", 0),
        "details": {
            "final_reply": final_reply,
            "graph_trajectory": trajectory["outputs"],
            "total_tokens": total_tokens,
            "model": model or os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL),
        },
    }
    if usage_metadata:
        outputs["details"]["usage_metadata"] = usage_metadata
    return outputs


def empty_outputs(*, error: str | None = None) -> dict:
    """Return a minimal outputs dict when graph invocation fails."""
    payload = {
        "output": "",
        "classification": "",
        "error_count": 1 if error else 0,
        "details": {
            "final_reply": "",
            "graph_trajectory": {"steps": [], "results": [], "inputs": []},
            "total_tokens": 0,
            "model": os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL),
        },
    }
    if error:
        payload["error"] = error
    return payload


def make_target(graph_factory: Callable[[HarnessConfig], Any], harness: HarnessConfig):
    """Create a LangSmith-compatible target function for a harness variant."""
    graph = graph_factory(harness)

    def target(inputs: dict) -> dict:
        """Run the agent on a single task input."""
        prompt = inputs.get("prompt", "")
        ticket_id = inputs.get("ticket_id", "")
        flaky_tools = inputs.get("flaky_tools")
        conversation_history = inputs.get("conversation_history")
        config = invoke_config(harness)
        if flaky_tools:
            config["configurable"]["flaky_tools"] = flaky_tools
        init_flaky_tools(flaky_tools)
        init_run_context()
        model_name = os.getenv("HARNESSLAB_MODEL", DEFAULT_MODEL)
        try:
            with get_usage_metadata_callback() as usage_cb:
                run_config = {**config, "callbacks": [usage_cb]}
                state = graph.invoke(
                    {
                        "messages": build_initial_messages(prompt, conversation_history),
                        "ticket_id": ticket_id,
                        "classification": "",
                        "final_reply": "",
                        "error_count": 0,
                    },
                    config=run_config,
                )
                callback_tokens, callback_model = aggregate_usage_metadata(usage_cb.usage_metadata)
                total_tokens = callback_tokens or message_tokens(state.get("messages", []))
                return extract_outputs(
                    state,
                    graph,
                    config,
                    total_tokens=total_tokens,
                    model=callback_model or model_name,
                    usage_metadata=usage_cb.usage_metadata or None,
                )
        except Exception as exc:  # noqa: BLE001 — always return outputs for evaluators
            return empty_outputs(error=str(exc))
        finally:
            clear_run_context()

    return target
