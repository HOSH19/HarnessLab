"""Tests for LangSmith SmithDB compatibility shims."""

from harnesslab.config import langsmith_compat as compat


def test_prefer_smithdb_experiment_traces_forces_dual_onto_v2(monkeypatch) -> None:
    """On dual backends, evaluate trace loading should use the SmithDB-only path."""
    from langsmith._internal import _v2_migration_utils
    from langsmith.evaluation import _runner

    monkeypatch.setattr(compat, "_PATCHED", False)
    # Restore a clean original so repeated test runs stay deterministic.
    if not hasattr(_runner, "_harnesslab_orig_load_traces"):
        _runner._harnesslab_orig_load_traces = _runner._load_traces_for_experiment
    monkeypatch.setattr(
        _runner, "_load_traces_for_experiment", _runner._harnesslab_orig_load_traces
    )

    seen: list[object] = []
    real_backend = _v2_migration_utils.get_query_backend

    def dual_backend(_flags):
        return _v2_migration_utils.QueryBackend.DUAL

    def fake_original(project, client, load_nested=False):
        seen.append(_v2_migration_utils.get_query_backend(None))
        return ["ok"]

    monkeypatch.setattr(_v2_migration_utils, "get_query_backend", dual_backend)
    monkeypatch.setattr(_runner, "_load_traces_for_experiment", fake_original)

    compat.prefer_smithdb_experiment_traces()
    result = _runner._load_traces_for_experiment("proj", client=None)

    assert result == ["ok"]
    assert seen == [_v2_migration_utils.QueryBackend.SMITHDB_ONLY]
    # Outside the wrapper, dual stays dual.
    assert _v2_migration_utils.get_query_backend(None) == (
        _v2_migration_utils.QueryBackend.DUAL
    )
    # Keep real backend available for other tests after this one ends.
    monkeypatch.setattr(_v2_migration_utils, "get_query_backend", real_backend)


def test_prefer_smithdb_experiment_traces_is_idempotent(monkeypatch) -> None:
    """Calling the shim twice must not stack wrappers."""
    from langsmith.evaluation import _runner

    monkeypatch.setattr(compat, "_PATCHED", False)
    if not hasattr(_runner, "_harnesslab_orig_load_traces"):
        _runner._harnesslab_orig_load_traces = _runner._load_traces_for_experiment
    monkeypatch.setattr(
        _runner, "_load_traces_for_experiment", _runner._harnesslab_orig_load_traces
    )

    before = _runner._load_traces_for_experiment
    compat.prefer_smithdb_experiment_traces()
    mid = _runner._load_traces_for_experiment
    compat.prefer_smithdb_experiment_traces()
    after = _runner._load_traces_for_experiment

    assert mid is after
    assert mid is not before
