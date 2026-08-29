"""Tests for example graph loader."""

from pathlib import Path

import pytest

from harnesslab.examples.loader import load_graph_factory


def test_load_research_agent_graph_factory() -> None:
    """Research agent exposes a build_graph factory."""
    root = Path(__file__).resolve().parents[1]
    factory = load_graph_factory(root / "examples" / "research_agent")
    assert callable(factory)
    assert factory.__name__ == "build_graph"


def test_load_incident_manager_graph_factory() -> None:
    """Incident manager exposes a build_graph factory."""
    root = Path(__file__).resolve().parents[1]
    factory = load_graph_factory(root / "examples" / "incident_manager")
    assert callable(factory)
    assert factory.__name__ == "build_graph"


def test_load_graph_factory_rejects_missing_example() -> None:
    """Unknown example paths raise a clear error."""
    root = Path(__file__).resolve().parents[1]
    with pytest.raises(ValueError, match="No graph module"):
        load_graph_factory(root / "examples" / "does_not_exist")
