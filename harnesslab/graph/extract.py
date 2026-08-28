"""Parse agent outputs from LangGraph message history.

Extracts classification and reply text from tool result messages.
Does not invoke models or access graph state beyond messages.
"""

import json
from typing import Any


def _parse_tool_content(content: Any) -> dict:
    """Parse tool message content into a dictionary when possible."""
    if isinstance(content, dict):
        return content
    if not isinstance(content, str):
        return {}
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw": content}


def _tool_calls_from_message(message: Any) -> list:
    """Return tool call objects from a LangChain message or serialized dict."""
    if isinstance(message, dict):
        return message.get("tool_calls", []) or []
    return getattr(message, "tool_calls", None) or []


def _tool_name_from_call(call: Any) -> str | None:
    """Extract a tool name from a tool call object or dict."""
    if isinstance(call, dict):
        if call.get("name"):
            return str(call["name"])
        function = call.get("function", {})
        if isinstance(function, dict) and function.get("name"):
            return str(function["name"])
        return None
    name = getattr(call, "name", None)
    if name:
        return str(name)
    return None


def serialize_messages(messages: list) -> list[dict[str, Any]]:
    """Convert LangChain messages into JSON-safe dicts for LangSmith outputs."""
    serialized: list[dict[str, Any]] = []
    for message in messages:
        if isinstance(message, dict):
            serialized.append(message)
            continue

        role = getattr(message, "type", "unknown")
        entry: dict[str, Any] = {
            "role": role,
            "content": getattr(message, "content", ""),
        }
        tool_calls = _tool_calls_from_message(message)
        if tool_calls:
            entry["tool_calls"] = [
                {"name": name}
                for call in tool_calls
                if (name := _tool_name_from_call(call)) is not None
            ]
        tool_name = getattr(message, "name", None)
        if tool_name:
            entry["name"] = tool_name
        serialized.append(entry)
    return serialized


def format_display_output(classification: str, reply: str) -> str:
    """Build a clean LangSmith output string without message role prefixes."""
    if classification and reply:
        return f"{classification}: {reply}"
    return reply or classification or ""


def extract_fields_from_messages(messages: list) -> dict[str, str]:
    """Extract classification and final reply from tool messages.

    Args:
        messages: LangGraph message list from final state.

    Returns:
        Dict with classification and final_reply string fields.
    """
    classification = ""
    final_reply = ""

    for message in messages:
        tool_name = None
        if isinstance(message, dict):
            tool_name = message.get("name")
        else:
            tool_name = getattr(message, "name", None)
        if not tool_name:
            continue

        payload = _parse_tool_content(
            message.get("content", "") if isinstance(message, dict) else getattr(message, "content", "")
        )
        if tool_name == "classify":
            classification = str(payload.get("category", classification))
        if tool_name == "draft_reply":
            final_reply = str(payload.get("reply", final_reply))

    return {
        "classification": classification,
        "final_reply": final_reply,
    }


def _tool_names_from_openai_message(message: dict) -> list[str]:
    """Extract tool names from one OpenAI-format trajectory message."""
    names: list[str] = []
    for call in message.get("tool_calls", []) or []:
        function = call.get("function", {}) if isinstance(call, dict) else {}
        name = function.get("name") if isinstance(function, dict) else None
        if name:
            names.append(str(name))
    return names


def extract_tool_names_from_messages(messages: list) -> list[str]:
    """Extract tool invocation names in order from LangChain messages.

    Args:
        messages: LangGraph message list from final state or run outputs.

    Returns:
        Ordered list of tool names observed in the message history.
    """
    names: list[str] = []
    for message in messages:
        for call in _tool_calls_from_message(message):
            name = _tool_name_from_call(call)
            if name:
                names.append(name)
    return names


def extract_tool_names_from_trajectory(graph_trajectory: dict) -> list[str]:
    """Extract tool names from graph trajectory result messages.

    Args:
        graph_trajectory: Trajectory dict attached to run outputs by the runner.

    Returns:
        Ordered list of tool names parsed from trajectory messages.
    """
    names: list[str] = []
    results = graph_trajectory.get("results", []) if graph_trajectory else []
    for result in results:
        if not isinstance(result, dict):
            continue
        for message in result.get("messages", []) or []:
            if isinstance(message, dict):
                names.extend(_tool_names_from_openai_message(message))
    return names


def extract_tool_names_from_outputs(outputs: dict) -> list[str]:
    """Extract tool names from run outputs using messages or trajectory data.

    Args:
        outputs: LangSmith run outputs dict.

    Returns:
        Ordered list of tool names from the best available source.
    """
    messages = outputs.get("messages")
    if messages:
        return extract_tool_names_from_messages(messages)
    return extract_tool_names_from_trajectory(outputs.get("graph_trajectory", {}))
