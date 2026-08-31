"""Harness configuration tests."""

from pathlib import Path

import pytest

from harnesslab.config.loader import load_harness_config


def test_load_minimal_harness() -> None:
    """Minimal harness YAML loads and validates."""
    root = Path(__file__).resolve().parents[1]
    config_path = root / "examples" / "research_agent" / "harnesses" / "minimal.yaml"
    config = load_harness_config(config_path)
    assert config.name == "minimal"
    assert config.execution.max_turns == 8
    assert config.tooling.retry_count == 0


def test_load_research_agent_cache_and_circuit_breaker() -> None:
    """Research agent ships cache and circuit_breaker harness presets."""
    root = Path(__file__).resolve().parents[1]
    harness_dir = root / "examples" / "research_agent" / "harnesses"

    cache = load_harness_config(harness_dir / "cache.yaml")
    assert cache.tooling.cache_reads is True
    assert cache.observability.langsmith_project == "research-agent"

    breaker = load_harness_config(harness_dir / "circuit_breaker.yaml")
    assert breaker.tooling.circuit_breaker_threshold == 2
    assert breaker.observability.langsmith_project == "research-agent"
