"""Load task JSON fixtures from an example project directory.

Reads task definitions for experiment datasets. Does not upload
to LangSmith; upload is owned by experiments.dataset.
"""

import json
from pathlib import Path


def load_tasks(tasks_dir: Path) -> list[dict]:
    """Load all task JSON files from a directory.

    Args:
        tasks_dir: Directory containing task-*.json files.

    Returns:
        List of task dicts with inputs and outputs for LangSmith.
    """
    tasks: list[dict] = []
    for path in sorted(tasks_dir.glob("task-*.json")):
        raw = json.loads(path.read_text())
        tasks.append(
            {
                "inputs": {
                    "prompt": raw["prompt"],
                    "ticket_id": raw["ticket_id"],
                },
                "outputs": {
                    "expected_category": raw["expected_category"],
                    "required_reply_terms": raw["required_reply_terms"],
                    "expected_nodes": raw.get("expected_nodes", []),
                },
            }
        )
    return tasks
