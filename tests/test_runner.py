"""Experiment runner helper tests."""

from pathlib import Path

from harnesslab.config.loader import load_harness_config
from harnesslab.experiments.runner import _experiment_metadata

_MAX_PROPAGATED_METADATA_LEN = 200


def test_experiment_metadata_uses_short_scalar_values() -> None:
    """Langfuse drops propagated metadata values longer than 200 characters."""
    root = Path(__file__).resolve().parents[1]
    harness = load_harness_config(
        root / "examples" / "ticket_triage" / "harnesses" / "retry.yaml"
    )

    metadata = _experiment_metadata(harness, model="gpt-4.1-nano")

    assert metadata["harness_name"] == "retry"
    assert metadata["model"] == "gpt-4.1-nano"
    assert metadata["retry_count"] == "2"
    assert "harnesslab" not in metadata
    for key, value in metadata.items():
        assert isinstance(value, str)
        assert len(value) <= _MAX_PROPAGATED_METADATA_LEN, (
            f"{key} exceeds Langfuse propagation limit"
        )
