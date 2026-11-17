"""GraphConfig YAML loader tests."""

from pathlib import Path

from harnesslab.config.graph_loader import default_react_graph, load_graph_config, load_graph_dir


def test_load_incident_graph_presets() -> None:
    """Incident manager ships react, pipeline, supervisor, plan_execute."""
    root = Path(__file__).resolve().parents[1]
    configs = load_graph_dir(root / "examples" / "incident_manager" / "graphs")
    assert "react" in configs
    assert configs["react"].topology == "react"
    assert configs["pipeline"].topology == "pipeline"
    assert configs["supervisor"].topology == "supervisor"
    assert configs["plan_execute"].topology == "plan_execute"
    assert configs["pipeline_verify"].require_verifier is True


def test_load_single_graph_yaml() -> None:
    """Single graph YAML validates name and topology."""
    root = Path(__file__).resolve().parents[1]
    config = load_graph_config(
        root / "examples" / "research_agent" / "graphs" / "supervisor.yaml"
    )
    assert config.name == "supervisor"
    assert config.max_workers == 3


def test_default_react_graph() -> None:
    """Built-in react baseline is available without YAML."""
    config = default_react_graph()
    assert config.name == "react"
    assert config.topology == "react"
