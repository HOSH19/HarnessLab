#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python3 -m pip install -e ".[dev]"
echo "Installed harnesslab. Run: python3 -m harnesslab --help"
