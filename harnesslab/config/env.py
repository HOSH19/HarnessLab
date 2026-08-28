"""Load local environment variables from a .env file."""

import logging
import os
from pathlib import Path


class LangfuseConfigError(RuntimeError):
    """Raised when Langfuse credentials or host are misconfigured."""


def _env_search_roots(*extra: Path) -> list[Path]:
    """Directories to walk upward when looking for a .env file."""
    roots: list[Path] = [Path.cwd().resolve()]

    try:
        roots.append(Path(__file__).resolve().parents[2])
    except IndexError:
        pass

    for path in extra:
        if path is not None:
            roots.append(path.resolve())

    return roots


def _find_env_file(*search_roots: Path) -> Path | None:
    """Return the first .env found by walking up from each search root."""
    seen: set[Path] = set()
    for root in search_roots:
        for directory in [root, *root.parents]:
            if directory in seen:
                continue
            seen.add(directory)
            candidate = directory / ".env"
            if candidate.is_file():
                return candidate
    return None


def load_local_env(*, example: Path | None = None) -> None:
    """Load key/value pairs from .env when python-dotenv is installed."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    extra = (example,) if example is not None else ()
    env_path = _find_env_file(*_env_search_roots(*extra))
    if env_path is not None:
        load_dotenv(env_path, override=False)


def disable_langfuse_tracing() -> None:
    """Turn off Langfuse tracing and uploads for local-only runs."""
    os.environ["LANGFUSE_TRACING_ENABLED"] = "false"
    logging.getLogger("langfuse").setLevel(logging.CRITICAL)


def validate_langfuse_upload_config() -> None:
    """Fail fast when Langfuse credentials cannot upload experiments."""
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if not public_key or not secret_key:
        raise LangfuseConfigError(
            "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are required without --local. "
            "Add them to .env or export them in your shell."
        )

    from langfuse import get_client

    try:
        if not get_client().auth_check():
            raise LangfuseConfigError("Langfuse auth_check() returned false.")
    except LangfuseConfigError:
        raise
    except Exception as exc:
        raise LangfuseConfigError(
            f"Langfuse is not reachable with the current credentials: {exc}"
        ) from exc
