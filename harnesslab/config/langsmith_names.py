"""LangSmith dataset and experiment naming for HarnessLab uploads."""

DEFAULT_LANGSMITH_DATASET = "graph engineering"
DEFAULT_EXPERIMENT_NAMESPACE = "graph-engineering"


def experiment_name(arm: str) -> str:
    """Build a LangSmith experiment prefix under the graph-engineering namespace."""
    prefix = f"{DEFAULT_EXPERIMENT_NAMESPACE}-"
    if arm.startswith(prefix):
        return arm
    return f"{prefix}{arm}"
