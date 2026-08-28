"""Upload task fixtures to a Langfuse dataset."""

from pathlib import Path

from langfuse import get_client

from harnesslab.experiments.tasks import load_tasks


def _get_or_create_dataset(client, dataset_name: str):
    """Return an existing dataset client or create a new dataset."""
    try:
        return client.get_dataset(dataset_name)
    except Exception:
        client.create_dataset(name=dataset_name, description="HarnessLab stress tasks")
        return client.get_dataset(dataset_name)


def ensure_dataset(
    tasks_dir: Path,
    dataset_name: str,
    *,
    task_limit: int | None = None,
    ticket_id: str | None = None,
) -> str:
    """Ensure a Langfuse dataset exists and matches local task fixtures."""
    client = get_client()
    tasks = load_tasks(tasks_dir, ticket_id=ticket_id)
    if task_limit is not None:
        tasks = tasks[:task_limit]

    _get_or_create_dataset(client, dataset_name)

    for task in tasks:
        ticket = task["inputs"].get("ticket_id", "")
        client.create_dataset_item(
            dataset_name=dataset_name,
            id=str(ticket) if ticket else None,
            input=task["inputs"],
            expected_output=task["outputs"],
            metadata={"source": "harnesslab"},
        )

    client.flush()
    return dataset_name


def upload_dataset(tasks_dir: Path, dataset_name: str) -> str:
    """Upload local task fixtures to Langfuse as a dataset."""
    return ensure_dataset(tasks_dir, dataset_name)
