"""Upload task fixtures to a Langfuse dataset.

Creates or updates datasets from local task JSON files.
Does not run agents or evaluators.
"""

from pathlib import Path

from langfuse import get_client

from harnesslab.experiments.tasks import load_tasks


def _get_or_create_dataset(client, dataset_name: str):
    """Return an existing dataset or create a new one."""
    try:
        client.create_dataset(name=dataset_name)
    except Exception:
        pass
    return client.get_dataset(dataset_name)


def _task_signature(tasks: list[dict]) -> list[tuple[str, str]]:
    """Build a stable signature from task ticket ids and prompts."""
    return [
        (task["inputs"].get("ticket_id", ""), task["inputs"].get("prompt", ""))
        for task in tasks
    ]


def ensure_dataset(
    tasks_dir: Path,
    dataset_name: str,
    *,
    task_limit: int | None = None,
    ticket_id: str | None = None,
) -> str:
    """Ensure a Langfuse dataset exists and matches local task fixtures.

    Args:
        tasks_dir: Directory containing task-*.json fixtures.
        dataset_name: Name for the Langfuse dataset.
        task_limit: Optional cap on number of tasks to sync.
        ticket_id: Optional filter to sync a single ticket fixture.

    Returns:
        Dataset name that was created or updated.
    """
    client = get_client()
    tasks = load_tasks(tasks_dir, ticket_id=ticket_id)
    if task_limit is not None:
        tasks = tasks[:task_limit]

    dataset = _get_or_create_dataset(client, dataset_name)
    existing_signature = [
        (
            (item.input or {}).get("ticket_id", ""),
            (item.input or {}).get("prompt", ""),
        )
        for item in dataset.items
    ]
    target_signature = _task_signature(tasks)

    if existing_signature != target_signature:
        for item in dataset.items:
            client.api.dataset_items.delete(id=item.id)
        for task in tasks:
            client.create_dataset_item(
                dataset_name=dataset_name,
                input=task["inputs"],
                expected_output=task["outputs"],
            )

    return dataset_name


def upload_dataset(tasks_dir: Path, dataset_name: str) -> str:
    """Upload local task fixtures to Langfuse as a dataset.

    Args:
        tasks_dir: Directory containing task-*.json fixtures.
        dataset_name: Name for the Langfuse dataset.

    Returns:
        Dataset name that was created or updated.
    """
    return ensure_dataset(tasks_dir, dataset_name)
