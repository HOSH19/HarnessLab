#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 -m pip install -e ".[dev]"

# pip --user installs console scripts to ~/.local/bin, which is often missing from PATH.
if ! grep -qE '(^|:)\$HOME/\.local/bin|\.local/bin' "$HOME/.bashrc" 2>/dev/null; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

export PATH="$HOME/.local/bin:$PATH"

# Many docs use `python`; Ubuntu images often ship only `python3`.
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"
if ! command -v python >/dev/null 2>&1; then
  ln -sf "$(command -v python3)" "$LOCAL_BIN/python"
fi

echo "Installed harnesslab."
echo "Run: harnesslab --help"
echo "Or:  python -m harnesslab --help"
