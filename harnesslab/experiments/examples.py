"""Convert task fixtures into LangSmith Example objects.

LangSmith evaluate requires Example schemas even when upload_results is
false. Task JSON loading is owned by experiments.tasks.
"""

from datetime import datetime, timezone
from uuid import uuid4

from langsmith.schemas import Example


def tasks_to_examples(tasks: list[dict]) -> list[Example]:
    """Build LangSmith Example objects from harness task dictionaries.

    Args:
        tasks: Task dicts with inputs and outputs keys.

    Returns:
        List of Example objects suitable for langsmith.evaluate data.
    """
    dataset_id = uuid4()
    timestamp = datetime.now(timezone.utc)

    return [
        Example(
            id=uuid4(),
            dataset_id=dataset_id,
            created_at=timestamp,
            modified_at=timestamp,
            inputs=task["inputs"],
            outputs=task["outputs"],
        )
        for task in tasks
    ]
