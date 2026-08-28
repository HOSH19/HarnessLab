"""Model catalog tests."""

from harnesslab.config.model_catalog import DEFAULT_CHEAP_MODELS, model_short_name, model_slug, parse_model_list


def test_parse_model_list_defaults_to_cheap_models() -> None:
    """Empty model string uses the cheap-model catalog."""
    assert parse_model_list(None) == list(DEFAULT_CHEAP_MODELS)
    assert parse_model_list("") == list(DEFAULT_CHEAP_MODELS)


def test_parse_model_list_splits_custom_models() -> None:
    """Comma-separated models are trimmed and parsed."""
    assert parse_model_list("gpt-4.1-nano, gpt-4.1-mini") == ["gpt-4.1-nano", "gpt-4.1-mini"]


def test_model_short_name_uses_one_word_labels() -> None:
    """Known models map to short experiment names."""
    assert model_short_name("gpt-4.1-nano") == "nano"
    assert model_short_name("gpt-4.1-mini") == "mini"
    assert model_short_name("gpt-3.5-turbo") == "turbo"


def test_model_slug_replaces_dots() -> None:
    """Model slugs are safe for filenames and experiment prefixes."""
    assert model_slug("gpt-4.1-nano") == "gpt-4-1-nano"
