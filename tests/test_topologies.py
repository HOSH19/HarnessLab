"""Topology compilers produce runnable graphs without calling an LLM."""

from pathlib import Path

from harnesslab.config.graph_loader import load_graph_config
from harnesslab.config.loader import load_harness_config
from harnesslab.examples.loader import load_graph_factory


def _compile(example: str, graph_name: str):
    root = Path(__file__).resolve().parents[1]
    example_path = root / "examples" / example
    harness = load_harness_config(example_path / "harnesses" / "minimal.yaml")
    graph = load_graph_config(example_path / "graphs" / f"{graph_name}.yaml")
    factory = load_graph_factory(example_path)
    return factory(harness, graph)


def test_incident_topologies_compile() -> None:
    """Each incident_manager topology compiles with a checkpointer."""
    for name in ("react", "pipeline", "pipeline_verify", "supervisor", "plan_execute"):
        compiled = _compile("incident_manager", name)
        assert compiled is not None
        assert hasattr(compiled, "invoke")


def test_research_topologies_compile() -> None:
    """Research agent topologies compile for parity."""
    for name in ("react", "pipeline", "supervisor", "plan_execute"):
        compiled = _compile("research_agent", name)
        assert compiled is not None
