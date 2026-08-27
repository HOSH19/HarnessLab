"""Load and validate harness YAML configuration files.

Handles file I/O and delegates schema validation to config.models.
Graph compilation is owned by graph.builder.
"""

from pathlib import Path

import yaml
from pydantic import ValidationError

from harnesslab.config.models import HarnessConfig


def load_harness_config(path: Path) -> HarnessConfig:
    """Load a harness config from a YAML file.

    Args:
        path: Path to a .yaml harness configuration file.

    Returns:
        Validated HarnessConfig instance.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValidationError: If YAML does not match HarnessConfig schema.
    """
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Harness config not found: {resolved}")

    raw = yaml.safe_load(resolved.read_text())
    return HarnessConfig.model_validate(raw)


def load_harness_dir(directory: Path) -> dict[str, HarnessConfig]:
    """Load all harness YAML files from a directory.

    Args:
        directory: Directory containing .yaml harness config files.

    Returns:
        Mapping of harness name to HarnessConfig.
    """
    configs: dict[str, HarnessConfig] = {}
    for yaml_path in sorted(directory.glob("*.yaml")):
        config = load_harness_config(yaml_path)
        configs[config.name] = config
    return configs
