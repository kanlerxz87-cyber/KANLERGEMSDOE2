#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Public pinned peer mirror only; not a substitute for organizer authentication.
# Use PYTHON=.venv/bin/python when the virtual environment is not activated.
PYTHON="${PYTHON:-python}"
"$PYTHON" scripts/restore_core_data.py --include-external
"$PYTHON" scripts/prepare_data.py
