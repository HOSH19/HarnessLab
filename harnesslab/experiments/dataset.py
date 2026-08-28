"""Upload task fixtures to a LangSmith dataset.

Creates or updates datasets from local task JSON files.
Does not run agents or evaluators.
"""

from pathlib import Path

from langsmith import Client

from harnesslab.experiments.tasks import load_tasks


def _get_or_create_dataset(client: Client, dataset_name: str):
    """Return an existing dataset or create a new one."""
    try:
        return client.create_dataset(dataset_name=dataset_name)
    except Exception:
        datasets = list(client.list_datasets(dataset_name=dataset_name))
        if not datasets:
            raise
        return datasets[0]


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
    """Ensure a LangSmith dataset exists and matches local task fixtures.

    Args:
        tasks_dir: Directory containing task-*.json fixtures.
        dataset_name: Name for the LangSmith dataset.
        task_limit: Optional cap on number of tasks to sync.
        ticket_id: Optional filter to sync a single ticket fixture.

    Returns:
        Dataset name that was created or updated.
    """
    client = Client()
    tasks = load_tasks(tasks_dir, ticket_id=ticket_id)
    if task_limit is not None:
        tasks = tasks[:task_limit]

    dataset = _get_or_create_dataset(client, dataset_name)
    existing_examples = list(client.list_examples(dataset_id=dataset.id))
    existing_signature = [
        (
            (example.inputs or {}).get("ticket_id", ""),
            (example.inputs or {}).get("prompt", ""),
        )
        for example in existing_examples
    ]
    target_signature = _task_signature(tasks)

    if existing_signature != target_signature:
        for example in existing_examples:
            client.delete_example(example_id=example.id)
        for task in tasks:
            client.create_example(
                inputs=task["inputs"],
                outputs=task["outputs"],
                dataset_id=dataset.id,
            )

    return dataset_name


def upload_dataset(tasks_dir: Path, dataset_name: str) -> str:
    """Upload local task fixtures to LangSmith as a dataset.

    Args:
        tasks_dir: Directory containing task-*.json fixtures.
        dataset_name: Name for the LangSmith dataset.

    Returns:
        Dataset name that was created or updated.
    """
    return ensure_dataset(tasks_dir, dataset_name)
