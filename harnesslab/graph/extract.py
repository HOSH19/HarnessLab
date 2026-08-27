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
        tool_name = getattr(message, "name", None)
        if not tool_name:
            continue

        payload = _parse_tool_content(getattr(message, "content", ""))
        if tool_name == "classify":
            classification = str(payload.get("category", classification))
        if tool_name == "draft_reply":
            final_reply = str(payload.get("reply", final_reply))

    return {
        "classification": classification,
        "final_reply": final_reply,
    }
