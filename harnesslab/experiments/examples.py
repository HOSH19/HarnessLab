"""Convert task fixtures into Langfuse local experiment items.

Langfuse run_experiment accepts LocalExperimentItem dicts when not using
hosted datasets. Task JSON loading is owned by experiments.tasks.
"""

from typing import Any


def tasks_to_examples(tasks: list[dict]) -> list[dict[str, Any]]:
    """Build Langfuse local experiment items from harness task dictionaries.

    Args:
        tasks: Task dicts with inputs and outputs keys.

    Returns:
        List of dicts suitable for langfuse.run_experiment data.
    """
    return [
        {
            "input": task["inputs"],
            "expected_output": task["outputs"],
        }
        for task in tasks
    ]
