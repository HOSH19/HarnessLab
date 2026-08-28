"""Load task JSON fixtures from an example project directory.

Reads task definitions for experiment datasets. Does not upload
to LangSmith; upload is owned by experiments.dataset.
"""

import json
from pathlib import Path


def load_tasks(tasks_dir: Path, *, ticket_id: str | None = None) -> list[dict]:
    """Load all task JSON files from a directory.

    Args:
        tasks_dir: Directory containing task-*.json files.
        ticket_id: Optional filter to a single ticket (e.g. T-011).

    Returns:
        List of task dicts with inputs and outputs for LangSmith.
    """
    tasks: list[dict] = []
    for path in sorted(tasks_dir.glob("task-*.json")):
        raw = json.loads(path.read_text())
        if ticket_id is not None and raw.get("ticket_id") != ticket_id:
            continue
        required_terms = raw.get("required_reply_terms", [])
        reply_hint = ""
        if required_terms:
            reply_hint = "include: " + ", ".join(required_terms)

        tasks.append(
            {
                "inputs": {
                    "prompt": raw["prompt"],
                    "ticket_id": raw["ticket_id"],
                    **({"flaky_tools": raw["flaky_tools"]} if "flaky_tools" in raw else {}),
                    **(
                        {"conversation_history": raw["conversation_history"]}
                        if "conversation_history" in raw
                        else {}
                    ),
                },
                "outputs": {
                    "expected_category": raw["expected_category"],
                    "final_reply": reply_hint,
                    "required_reply_terms": required_terms,
                    "expected_nodes": raw.get("expected_nodes", []),
                    **({"expected_tools": raw["expected_tools"]} if "expected_tools" in raw else {}),
                    **(
                        {"expected_max_steps": raw["expected_max_steps"]}
                        if "expected_max_steps" in raw
                        else {}
                    ),
                    **(
                        {"max_acceptable_errors": raw["max_acceptable_errors"]}
                        if "max_acceptable_errors" in raw
                        else {}
                    ),
                    **({"stress": raw["stress"]} if "stress" in raw else {}),
                },
            }
        )
    return tasks
