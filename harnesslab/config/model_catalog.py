"""Cheap model catalog for HarnessLab model-comparison experiments."""

# OpenAI models suitable for low-cost harness and model A/B testing.
# Avoid premium models (gpt-4o, gpt-4.1, o-series) in default compare runs.
DEFAULT_CHEAP_MODELS: tuple[str, ...] = (
    "gpt-4.1-nano",
    "gpt-4o-mini",
    "gpt-3.5-turbo",
)

DEFAULT_MODEL = DEFAULT_CHEAP_MODELS[0]

# Short labels for experiment names (what varies in model-comparison runs).
MODEL_SHORT_NAMES: dict[str, str] = {
    "gpt-4.1-nano": "nano",
    "gpt-4o-mini": "mini",
    "gpt-3.5-turbo": "turbo",
}


def parse_model_list(models: str | None) -> list[str]:
    """Parse a comma-separated model list or return the cheap-model defaults."""
    if not models or not models.strip():
        return list(DEFAULT_CHEAP_MODELS)
    return [name.strip() for name in models.split(",") if name.strip()]


def model_slug(model: str) -> str:
    """Return a filesystem-safe slug for experiment names."""
    return model.replace(".", "-").replace("/", "_")


def model_short_name(model: str) -> str:
    """Return a short experiment label for a model (1 word when possible)."""
    return MODEL_SHORT_NAMES.get(model, model_slug(model))
