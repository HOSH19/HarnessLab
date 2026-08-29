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
