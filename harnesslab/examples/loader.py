"""Load graph factories from example project directories."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from harnesslab.config.models import HarnessConfig


def load_graph_factory(example: Path) -> Callable[[HarnessConfig], Any]:
    """Import and return the build_graph callable for an example project.

    Looks for ``build_graph`` first, then ``build_<example_name>_graph``.
    """
    example = example.resolve()
    module_name = f"examples.{example.name}.graph"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise ValueError(f"No graph module at {example / 'graph.py'}") from exc

    factory = getattr(module, "build_graph", None)
    if factory is None:
        factory = getattr(module, f"build_{example.name}_graph", None)
    if factory is None:
        raise ValueError(
            f"{module_name} must define build_graph or build_{example.name}_graph"
        )
    return factory
