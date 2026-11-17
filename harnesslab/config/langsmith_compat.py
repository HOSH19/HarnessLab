"""Compatibility shims for LangSmith SDK gaps (SmithDB migration).

``langsmith.evaluate`` still calls deprecated ``Client.list_runs`` on dual
ClickHouse+SmithDB Cloud backends (see langchain-ai/langsmith-python#108).
Prefer the SmithDB v2 loader whenever SmithDB queries are available so
HarnessLab API keys stop accumulating deprecated ``POST /runs/query`` usage.
"""

from __future__ import annotations

_PATCHED = False


def prefer_smithdb_experiment_traces() -> None:
    """Route evaluate experiment-trace loads through SmithDB on dual backends."""
    global _PATCHED
    if _PATCHED:
        return

    try:
        from langsmith._internal import _v2_migration_utils
        from langsmith.evaluation import _runner
    except ImportError:
        return

    original = _runner._load_traces_for_experiment
    original_backend = _v2_migration_utils.get_query_backend

    def _prefer_smithdb(instance_flags):
        backend = original_backend(instance_flags)
        if backend == _v2_migration_utils.QueryBackend.DUAL:
            return _v2_migration_utils.QueryBackend.SMITHDB_ONLY
        return backend

    def _load_traces_for_experiment(project, client, load_nested: bool = False):
        previous = _v2_migration_utils.get_query_backend
        _v2_migration_utils.get_query_backend = _prefer_smithdb
        try:
            return original(project, client, load_nested=load_nested)
        finally:
            _v2_migration_utils.get_query_backend = previous

    _runner._load_traces_for_experiment = _load_traces_for_experiment
    _PATCHED = True
