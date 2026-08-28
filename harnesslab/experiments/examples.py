"""Convert task fixtures into local Langfuse experiment items."""

from typing import Any


def tasks_to_local_items(tasks: list[dict]) -> list[dict[str, Any]]:
    """Build local experiment items from harness task dictionaries."""
    return [
        {
            "input": task["inputs"],
            "expected_output": task["outputs"],
            "metadata": {"ticket_id": task["inputs"].get("ticket_id")},
        }
        for task in tasks
    ]
