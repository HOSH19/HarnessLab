"""Environment helper tests."""

import os

import pytest

from harnesslab.config.env import (
    LangSmithConfigError,
    disable_langsmith_tracing,
    validate_langsmith_upload_config,
)


def test_disable_langsmith_tracing_sets_env(monkeypatch) -> None:
    """Local mode disables LangSmith tracing environment flags."""
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")

    disable_langsmith_tracing()

    assert os.environ["LANGSMITH_TRACING"] == "false"
    assert os.environ["LANGCHAIN_TRACING_V2"] == "false"


def test_validate_langsmith_upload_config_requires_api_key(monkeypatch) -> None:
    """Upload validation fails when the API key is missing."""
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    with pytest.raises(LangSmithConfigError, match="LANGSMITH_API_KEY"):
        validate_langsmith_upload_config()
