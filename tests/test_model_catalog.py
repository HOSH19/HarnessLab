"""Model catalog tests."""

from harnesslab.config.model_catalog import DEFAULT_CHEAP_MODELS, model_slug, parse_model_list


def test_parse_model_list_defaults_to_cheap_models() -> None:
    """Empty model string uses the cheap-model catalog."""
    assert parse_model_list(None) == list(DEFAULT_CHEAP_MODELS)
    assert parse_model_list("") == list(DEFAULT_CHEAP_MODELS)


def test_parse_model_list_splits_custom_models() -> None:
    """Comma-separated models are trimmed and parsed."""
    assert parse_model_list("gpt-4.1-nano, gpt-4o-mini") == ["gpt-4.1-nano", "gpt-4o-mini"]


def test_model_slug_replaces_dots() -> None:
    """Model slugs are safe for filenames and experiment prefixes."""
    assert model_slug("gpt-4.1-nano") == "gpt-4-1-nano"
