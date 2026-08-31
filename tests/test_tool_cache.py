"""Tool cache middleware tests."""

from harnesslab.middleware.cache import CACHEABLE_TOOLS, cache_key, get_cached_result, store_cached_result
from harnesslab.middleware.runtime import init_run_context


def test_cache_key_is_stable() -> None:
    """Cache keys are stable for identical arguments."""
    key_a = cache_key("read_incident", ("I-101",), {})
    key_b = cache_key("read_incident", ("I-101",), {})
    assert key_a == key_b


def test_store_and_get_cached_read_tool() -> None:
    """Read tools can be cached within a run context."""
    context = init_run_context()
    key = cache_key("read_incident", ("I-101",), {})
    assert get_cached_result("read_incident", key, context) is None
    store_cached_result("read_incident", key, '{"id":"I-101"}', context)
    assert get_cached_result("read_incident", key, context) == '{"id":"I-101"}'


def test_non_cacheable_tools_are_ignored() -> None:
    """Only configured read tools participate in caching."""
    context = init_run_context()
    key = cache_key("classify", ("infra",), {})
    store_cached_result("classify", key, "ok", context)
    assert get_cached_result("classify", key, context) is None
    assert "classify" not in CACHEABLE_TOOLS
