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


def extract_fields_from_messages(messages: list) -> dict[str, str]:
    """Extract classification and final reply from tool messages."""
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


def extract_tool_names_from_messages(messages: list) -> list[str]:
    """Extract tool invocation names in order from LangChain messages."""
    names: list[str] = []
    for message in messages:
        for call in _tool_calls_from_message(message):
            name = _tool_name_from_call(call)
            if name:
                names.append(name)
    return names
