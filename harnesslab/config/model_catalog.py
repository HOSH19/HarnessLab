"""Cheap model catalog for HarnessLab model-comparison experiments."""

# OpenAI models suitable for low-cost harness and model A/B testing.
# All defaults are cheaper than gpt-4o-mini; override with --models if needed.
DEFAULT_CHEAP_MODELS: tuple[str, ...] = (
    "gpt-4.1-nano",
    "gpt-4.1-mini",
    "gpt-3.5-turbo",
)

DEFAULT_MODEL = DEFAULT_CHEAP_MODELS[0]

# Short labels for experiment names (what varies in model-comparison runs).
MODEL_SHORT_NAMES: dict[str, str] = {
    "gpt-4.1-nano": "nano",
    "gpt-4.1-mini": "mini",
    "gpt-3.5-turbo": "turbo",
}

# Approximate USD per 1K tokens (input+output blended) for portfolio cost estimates.
MODEL_COST_PER_1K_TOKENS: dict[str, float] = {
    "gpt-4.1-nano": 0.0001,
    "gpt-4.1-mini": 0.0004,
    "gpt-3.5-turbo": 0.0005,
}

DEFAULT_COST_PER_1K = 0.0002


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


def model_cost_per_1k_tokens(model: str) -> float:
    """Return approximate blended USD cost per 1K tokens for a model."""
    return MODEL_COST_PER_1K_TOKENS.get(model, DEFAULT_COST_PER_1K)
