"""Environment helper tests."""

import os
from pathlib import Path

import pytest

from harnesslab.config.env import (
    LangSmithConfigError,
    _find_env_file,
    disable_langsmith_tracing,
    load_local_env,
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


def test_find_env_file_walks_up_from_search_root(tmp_path: Path, monkeypatch) -> None:
    """A .env file is found in a parent of the search root."""
    monkeypatch.chdir(tmp_path)
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    env_file = tmp_path / ".env"
    env_file.write_text("LANGSMITH_API_KEY=test\n", encoding="utf-8")

    assert _find_env_file(nested) == env_file


def test_load_local_env_from_package_root_when_cwd_has_no_env(
    tmp_path: Path, monkeypatch
) -> None:
    """Keys load from the HarnessLab project root even when cwd lacks .env."""
    monkeypatch.chdir(tmp_path)
    project_root = tmp_path / "harnesslab"
    project_root.mkdir()
    (project_root / ".env").write_text(
        "HARNESSLAB_MODEL=from-nested-root\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        "harnesslab.config.env._env_search_roots",
        lambda *extra: [tmp_path.resolve(), project_root.resolve()],
    )
    monkeypatch.delenv("HARNESSLAB_MODEL", raising=False)

    load_local_env()

    assert os.getenv("HARNESSLAB_MODEL") == "from-nested-root"
