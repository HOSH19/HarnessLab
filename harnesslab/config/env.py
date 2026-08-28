"""Load local environment variables from a .env file.

Reads a project-root .env for local development only. Does not override
variables that are already set in the shell environment.
"""

from pathlib import Path


def load_local_env() -> None:
    """Load key/value pairs from .env when python-dotenv is installed."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
