#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 -m pip install -e ".[dev]"

# pip --user installs console scripts to ~/.local/bin, which is often missing from PATH.
if ! grep -qE '(^|:)\$HOME/\.local/bin|\.local/bin' "$HOME/.bashrc" 2>/dev/null; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

export PATH="$HOME/.local/bin:$PATH"

echo "Installed harnesslab."
echo "Run: harnesslab --help"
echo "Or:  python3 -m harnesslab --help"
