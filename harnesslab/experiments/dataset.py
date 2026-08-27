"""Upload task fixtures to a LangSmith dataset.

Creates or updates datasets from local task JSON files.
Does not run agents or evaluators.
"""

from pathlib import Path

from langsmith import Client

from harnesslab.experiments.tasks import load_tasks


def upload_dataset(tasks_dir: Path, dataset_name: str) -> str:
    """Upload local task fixtures to LangSmith as a dataset.

    Args:
        tasks_dir: Directory containing task-*.json fixtures.
        dataset_name: Name for the LangSmith dataset.

    Returns:
        Dataset name that was created or updated.
    """
    client = Client()
    tasks = load_tasks(tasks_dir)

    try:
        dataset = client.create_dataset(dataset_name=dataset_name)
    except Exception:
        datasets = list(client.list_datasets(dataset_name=dataset_name))
        if not datasets:
            raise
        dataset = datasets[0]

    for task in tasks:
        client.create_example(
            inputs=task["inputs"],
            outputs=task["outputs"],
            dataset_id=dataset.id,
        )

    return dataset_name