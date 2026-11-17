"""Load and validate graph topology YAML configuration files."""

from pathlib import Path

import yaml

from harnesslab.config.graph_models import GraphConfig


def load_graph_config(path: Path) -> GraphConfig:
    """Load a graph config from a YAML file.

    Args:
        path: Path to a .yaml graph configuration file.

    Returns:
        Validated GraphConfig instance.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValidationError: If YAML does not match GraphConfig schema.
    """
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Graph config not found: {resolved}")

    raw = yaml.safe_load(resolved.read_text()) or {}
    return GraphConfig.model_validate(raw)


def load_graph_dir(directory: Path) -> dict[str, GraphConfig]:
    """Load all graph YAML files from a directory.

    Args:
        directory: Directory containing .yaml graph config files.

    Returns:
        Mapping of graph name to GraphConfig.
    """
    configs: dict[str, GraphConfig] = {}
    for yaml_path in sorted(directory.glob("*.yaml")):
        config = load_graph_config(yaml_path)
        configs[config.name] = config
    return configs


def default_react_graph() -> GraphConfig:
    """Return the built-in single-agent ReAct baseline when no YAML exists."""
    return GraphConfig(name="react", topology="react")
