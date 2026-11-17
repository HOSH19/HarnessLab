"""Model catalog tests."""

from harnesslab.config.model_catalog import DEFAULT_CHEAP_MODELS, DEFAULT_MODEL, model_short_name, model_slug, parse_model_list


def test_parse_model_list_defaults_to_cheap_models() -> None:
    """Empty model string uses the cheap-model catalog."""
    assert parse_model_list(None) == list(DEFAULT_CHEAP_MODELS)
    assert parse_model_list("") == list(DEFAULT_CHEAP_MODELS)
    assert DEFAULT_MODEL == "gpt-4o-mini"


def test_parse_model_list_splits_custom_models() -> None:
    """Comma-separated models are trimmed and parsed."""
    assert parse_model_list("gpt-4o-mini, gpt-4o") == ["gpt-4o-mini", "gpt-4o"]


def test_model_short_name_uses_one_word_labels() -> None:
    """Known models map to short experiment names."""
    assert model_short_name("gpt-4o-mini") == "mini"
    assert model_short_name("gpt-4o") == "4o"
    assert model_short_name("gpt-3.5-turbo") == "turbo"


def test_model_slug_replaces_dots() -> None:
    """Model slugs are safe for filenames and experiment prefixes."""
    assert model_slug("gpt-4o-mini") == "gpt-4o-mini"
    assert model_slug("gpt-3.5-turbo") == "gpt-3-5-turbo"
