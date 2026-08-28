"""Load local environment variables from a .env file.

Reads a project-root .env for local development only. Does not override
variables that are already set in the shell environment.
"""

import logging
import os
from pathlib import Path


class LangSmithConfigError(RuntimeError):
    """Raised when LangSmith credentials or endpoint are misconfigured."""


def _env_search_roots(*extra: Path) -> list[Path]:
    """Directories to walk upward when looking for a .env file."""
    roots: list[Path] = [Path.cwd().resolve()]

    # Editable installs: harnesslab/harnesslab/config/env.py -> project root
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
    """Load key/value pairs from .env when python-dotenv is installed.

    Searches the current working directory, the HarnessLab project root,
    and (optionally) the example path and their ancestors. Does not
    override variables already set in the shell environment.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    extra = (example,) if example is not None else ()
    env_path = _find_env_file(*_env_search_roots(*extra))
    if env_path is not None:
        load_dotenv(env_path, override=False)


def disable_langsmith_tracing() -> None:
    """Turn off LangSmith tracing and uploads for local-only runs."""
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

    logging.getLogger("langsmith").setLevel(logging.CRITICAL)

    try:
        import langsmith as ls

        ls.configure(enabled=False)
    except Exception:
        pass


def validate_langsmith_upload_config() -> None:
    """Fail fast when LangSmith credentials cannot upload experiments."""
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        raise LangSmithConfigError(
            "LANGSMITH_API_KEY is required without --local. "
            "Add it to .env or export it in your shell."
        )

    from langsmith import Client

    try:
        list(Client().list_datasets(limit=1))
    except Exception as exc:
        message = str(exc)
        if "403" in message:
            raise LangSmithConfigError(
                "LangSmith returned 403 Forbidden. Common causes:\n"
                "  • Your account is in a non-US region — set LANGSMITH_ENDPOINT in .env\n"
                "    APAC: https://apac.api.smith.langchain.com\n"
                "    EU:   https://eu.api.smith.langchain.com\n"
                "  • Your API key lacks workspace permissions — regenerate it in LangSmith\n"
                f"Original error: {exc}"
            ) from exc
        raise LangSmithConfigError(
            f"LangSmith is not reachable with the current credentials: {exc}"
        ) from exc
